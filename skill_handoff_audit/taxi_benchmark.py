from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from math import exp
from typing import Iterable

import gymnasium as gym
import numpy as np


LANDMARK_NAMES = ("R", "G", "Y", "B")
LANDMARK_LOCS = ((0, 0), (0, 4), (4, 0), (4, 3))
MOVE_ACTIONS = (0, 1, 2, 3)
PICKUP = 4
DROPOFF = 5
NUM_TAXI_STATES = 500
NUM_TAXI_ACTIONS = 6


def _build_transition_table() -> tuple[tuple[tuple[int, float, bool], ...], ...]:
    env = gym.make("Taxi-v3")
    try:
        return tuple(
            tuple(
                (
                    int(env.unwrapped.P[state][action][0][1]),
                    float(env.unwrapped.P[state][action][0][2]),
                    bool(env.unwrapped.P[state][action][0][3]),
                )
                for action in range(NUM_TAXI_ACTIONS)
            )
            for state in range(NUM_TAXI_STATES)
        )
    finally:
        env.close()


TRANSITIONS = _build_transition_table()


@dataclass(frozen=True)
class TaxiDiagnostics:
    pickup_violation: float
    dropoff_violation: float
    route_excess: float
    boundary_surprise: float
    handoff_estimate: float
    estimated_steps: int

    @property
    def public_boundary_risk(self) -> float:
        return (
            1.10 * self.pickup_violation
            + 1.30 * self.dropoff_violation
            + 0.08 * self.route_excess
            + 0.75 * self.boundary_surprise
            - 0.55 * self.handoff_estimate
        )


@dataclass(frozen=True)
class TaxiCandidate:
    chain: tuple[str, ...]
    proxy_score: float
    diagnostics: TaxiDiagnostics
    true_return: float
    success: float
    primitive_steps: int

    def public_row(self) -> dict[str, float | str]:
        return {
            "chain": "->".join(self.chain),
            "proxy_score": self.proxy_score,
            "true_return": self.true_return,
            "success": self.success,
            "primitive_steps": self.primitive_steps,
            "pickup_violation": self.diagnostics.pickup_violation,
            "dropoff_violation": self.diagnostics.dropoff_violation,
            "route_excess": self.diagnostics.route_excess,
            "boundary_surprise": self.diagnostics.boundary_surprise,
            "handoff_estimate": self.diagnostics.handoff_estimate,
            "public_boundary_risk": self.diagnostics.public_boundary_risk,
        }


def nav_option(landmark: int) -> str:
    return f"nav_{LANDMARK_NAMES[int(landmark)]}"


def _nav_target(option: str) -> int:
    if not option.startswith("nav_"):
        raise ValueError(option)
    return LANDMARK_NAMES.index(option[-1])


@lru_cache(maxsize=None)
def decode_state(obs: int) -> tuple[int, int, int, int]:
    out = int(obs)
    dest = out % 4
    out //= 4
    passenger = out % 5
    out //= 5
    col = out % 5
    out //= 5
    row = out
    return int(row), int(col), int(passenger), int(dest)


@lru_cache(maxsize=None)
def _encode(row: int, col: int, passenger: int, dest: int) -> int:
    return int((((int(row) * 5 + int(col)) * 5 + int(passenger)) * 4) + int(dest))


@lru_cache(maxsize=None)
def taxi_transition(state: int, action: int) -> tuple[int, float, bool]:
    return TRANSITIONS[int(state)][int(action)]


def taxi_initial_states(seed: int, count: int) -> list[int]:
    env = gym.make("Taxi-v3")
    states: list[int] = []
    try:
        for i in range(int(count)):
            obs, _ = env.reset(seed=int(seed) * 1000 + i)
            states.append(int(obs))
    finally:
        env.close()
    return states


@lru_cache(maxsize=None)
def shortest_nav_actions(obs: int, target_landmark: int) -> tuple[int, ...]:
    target = LANDMARK_LOCS[int(target_landmark)]
    start = int(obs)
    queue: deque[tuple[int, tuple[int, ...]]] = deque([(start, tuple())])
    visited = {start}
    env = gym.make("Taxi-v3")
    try:
        while queue:
            state, actions = queue.popleft()
            row, col, _, _ = decode_state(state)
            if (row, col) == target:
                return actions
            for action in MOVE_ACTIONS:
                next_state, _, _ = taxi_transition(state, action)
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, actions + (int(action),)))
    finally:
        env.close()
    raise RuntimeError(f"no Taxi route from {obs} to {target_landmark}")


def canonical_chain(obs: int) -> tuple[str, ...]:
    _, _, passenger, dest = decode_state(obs)
    if passenger == 4:
        return (nav_option(dest), "dropoff")
    return (nav_option(passenger), "pickup", nav_option(dest), "dropoff")


def _abstract_diagnostics(obs: int, chain: Iterable[str]) -> TaxiDiagnostics:
    row, col, passenger, dest = decode_state(obs)
    taxi_loc: int | None = None
    for idx, loc in enumerate(LANDMARK_LOCS):
        if (row, col) == loc:
            taxi_loc = idx
            break
    onboard = passenger == 4
    delivered = False
    pickup_violation = 0.0
    dropoff_violation = 0.0
    boundary_surprise = 0.0
    route_steps = 0
    direct_steps = 0
    current_obs = int(obs)

    for option in chain:
        if option.startswith("nav_"):
            target = _nav_target(option)
            actions = shortest_nav_actions(current_obs, target)
            route_steps += len(actions)
            direct_steps += abs(row - LANDMARK_LOCS[target][0]) + abs(col - LANDMARK_LOCS[target][1])
            row, col = LANDMARK_LOCS[target]
            taxi_loc = target
            current_obs = _encode(row, col, 4 if onboard else passenger, dest)
            continue
        if option == "pickup":
            if onboard:
                pickup_violation += 1.0
                boundary_surprise += 0.5
            elif taxi_loc == passenger:
                onboard = True
                current_obs = _encode(row, col, 4, dest)
            else:
                pickup_violation += 1.0 + 0.35 * abs((taxi_loc if taxi_loc is not None else -1) - passenger)
                boundary_surprise += 1.0
            route_steps += 1
            continue
        if option == "dropoff":
            if onboard and taxi_loc == dest:
                onboard = False
                delivered = True
                current_obs = _encode(row, col, dest, dest)
            else:
                dropoff_violation += 1.0 + (0.5 if not onboard else 0.0)
                if taxi_loc is None or taxi_loc != dest:
                    dropoff_violation += 0.35
                boundary_surprise += 1.0
            route_steps += 1
            continue
        raise ValueError(option)

    if not delivered:
        dropoff_violation += 0.8
        boundary_surprise += 0.6
    route_excess = max(0.0, float(route_steps - direct_steps - 2))
    handoff_estimate = exp(-1.35 * pickup_violation - 1.55 * dropoff_violation - 0.28 * boundary_surprise)
    return TaxiDiagnostics(
        pickup_violation=float(pickup_violation),
        dropoff_violation=float(dropoff_violation),
        route_excess=float(route_excess),
        boundary_surprise=float(boundary_surprise),
        handoff_estimate=float(max(0.0, min(1.0, handoff_estimate))),
        estimated_steps=int(route_steps),
    )


@lru_cache(maxsize=None)
def execute_chain(obs: int, chain: Iterable[str]) -> tuple[float, float, int]:
    total = 0.0
    steps = 0
    state = int(obs)
    for option in chain:
        if option.startswith("nav_"):
            actions = shortest_nav_actions(state, _nav_target(option))
        elif option == "pickup":
            actions = (PICKUP,)
        elif option == "dropoff":
            actions = (DROPOFF,)
        else:
            raise ValueError(option)
        for action in actions:
            state, reward, terminated = taxi_transition(state, int(action))
            total += float(reward)
            steps += 1
            if terminated:
                passenger = decode_state(state)[2]
                return total, float(passenger == decode_state(state)[3]), steps
    _, _, passenger, dest = decode_state(state)
    return total, float(passenger == dest), steps


def taxi_proxy_score(chain: tuple[str, ...], diagnostics: TaxiDiagnostics, obs: int) -> float:
    _, _, passenger, dest = decode_state(obs)
    navs = [option for option in chain if option.startswith("nav_")]
    has_pickup = float("pickup" in chain)
    has_dropoff = float("dropoff" in chain)
    dest_visits = sum(1 for option in navs if _nav_target(option) == dest)
    passenger_visits = 0 if passenger == 4 else sum(1 for option in navs if _nav_target(option) == passenger)
    unique_navs = len(set(navs))
    ambition = 2.4 * unique_navs + 2.2 * dest_visits + 1.2 * len(chain)
    task_tokens = 10.0 * has_pickup + 15.0 * has_dropoff + 1.0 * passenger_visits
    weak_boundary_penalty = 1.0 * diagnostics.pickup_violation + 1.2 * diagnostics.dropoff_violation
    return float(task_tokens + ambition - 0.04 * diagnostics.estimated_steps - weak_boundary_penalty)


def evaluate_candidate(obs: int, chain: Iterable[str]) -> TaxiCandidate:
    chain_tuple = tuple(chain)
    diagnostics = _abstract_diagnostics(int(obs), chain_tuple)
    true_return, success, steps = execute_chain(int(obs), chain_tuple)
    proxy = taxi_proxy_score(chain_tuple, diagnostics, int(obs))
    return TaxiCandidate(
        chain=chain_tuple,
        proxy_score=proxy,
        diagnostics=diagnostics,
        true_return=true_return,
        success=success,
        primitive_steps=steps,
    )


def sample_candidate_chains(obs: int, n: int, seed: int) -> list[tuple[str, ...]]:
    rng = np.random.default_rng(int(seed))
    _, _, passenger, dest = decode_state(obs)
    landmarks = list(range(4))
    passenger_target = int(dest if passenger == 4 else passenger)
    chains: list[tuple[str, ...]] = [canonical_chain(obs)]
    templates = [
        (nav_option(dest), "pickup", nav_option(passenger_target), "dropoff"),
        (nav_option(dest), "dropoff", nav_option(passenger_target), "pickup", nav_option(dest), "dropoff"),
        (nav_option(passenger_target), nav_option(dest), "pickup", "dropoff"),
        (nav_option(dest), nav_option(passenger_target), "pickup", "dropoff"),
        (nav_option(passenger_target), "pickup", nav_option((dest + 1) % 4), "dropoff"),
    ]
    chains.extend(templates)
    while len(chains) < int(n):
        first = int(rng.choice(landmarks))
        second = int(rng.choice(landmarks))
        third = int(rng.choice(landmarks))
        if rng.random() < 0.45:
            chain = (nav_option(first), "pickup", nav_option(second), "dropoff")
        elif rng.random() < 0.75:
            chain = (nav_option(first), "dropoff", nav_option(second), "pickup", nav_option(third), "dropoff")
        else:
            chain = (nav_option(first), nav_option(second), "pickup", nav_option(third), "dropoff")
        chains.append(chain)
    return chains[: int(n)]


def select_handoff_sieve(candidates: list[TaxiCandidate], penalty: float = 7.5) -> TaxiCandidate:
    return max(candidates, key=lambda cand: cand.proxy_score - penalty * cand.diagnostics.public_boundary_risk)
