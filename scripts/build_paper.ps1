$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Paper = Join-Path $Root "paper"
$Final = Join-Path $Paper "final"
$Downloads = Join-Path $HOME "Downloads"
$DownloadPdf = Join-Path $Downloads "iclr_submission_hierarchical_options.pdf"
$DesktopPdf = Join-Path (Join-Path $HOME "OneDrive\Desktop") "best of n hierarchical skill options-v2.pdf"
$Log = Join-Path $Final "build_log.md"

New-Item -ItemType Directory -Force -Path $Final | Out-Null
New-Item -ItemType Directory -Force -Path $Downloads | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DesktopPdf) | Out-Null

$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
$bibtex = Get-Command bibtex -ErrorAction SilentlyContinue
$compiled = $false
$messages = New-Object System.Collections.Generic.List[string]
$messages.Add("# Paper Build Log")
$messages.Add("")
$messages.Add("Build time: $(Get-Date -Format o)")

if ($pdflatex -and $bibtex) {
  Push-Location $Paper
  try {
    foreach ($Scratch in @("main.aux", "main.bbl", "main.blg", "main.log", "main.out")) {
      $ScratchPath = Join-Path $Paper $Scratch
      if (Test-Path $ScratchPath) {
        Remove-Item -LiteralPath $ScratchPath -Force
      }
    }
    $messages.Add("Using pdflatex: $($pdflatex.Source)")
    $messages.Add("Using bibtex: $($bibtex.Source)")
    & pdflatex -interaction=nonstopmode -halt-on-error main.tex | Tee-Object -FilePath (Join-Path $Final "pdflatex_1.log") | Out-Null
    & bibtex main | Tee-Object -FilePath (Join-Path $Final "bibtex.log") | Out-Null
    & pdflatex -interaction=nonstopmode -halt-on-error main.tex | Tee-Object -FilePath (Join-Path $Final "pdflatex_2.log") | Out-Null
    & pdflatex -interaction=nonstopmode -halt-on-error main.tex | Tee-Object -FilePath (Join-Path $Final "pdflatex_3.log") | Out-Null
    Copy-Item -Force (Join-Path $Paper "main.pdf") (Join-Path $Final "iclr_submission.pdf")
    $compiled = $true
    $messages.Add("Status: compiled LaTeX successfully.")
  }
  catch {
    $messages.Add("Status: LaTeX compilation failed.")
    $messages.Add("Failure: $($_.Exception.Message)")
  }
  finally {
    Pop-Location
  }
}
else {
  $messages.Add("Status: local TeX toolchain unavailable.")
  if (-not $pdflatex) { $messages.Add("Missing: pdflatex") }
  if (-not $bibtex) { $messages.Add("Missing: bibtex") }
}

if (-not $compiled) {
  $messages.Add("Action: generating fallback PDF with matplotlib from paper/build_fallback_pdf.py.")
  Push-Location $Root
  try {
    python "paper\build_fallback_pdf.py" | Tee-Object -FilePath (Join-Path $Final "fallback.log") | Out-Null
  }
  finally {
    Pop-Location
  }
}

$RepoPdf = Join-Path $Final "iclr_submission.pdf"
if (Test-Path $RepoPdf) {
  Copy-Item -Force $RepoPdf $DownloadPdf
  Copy-Item -Force $RepoPdf $DesktopPdf
  $messages.Add("Repository PDF: $RepoPdf")
  $messages.Add("Downloads PDF: $DownloadPdf")
  $messages.Add("Desktop PDF: $DesktopPdf")
}
else {
  $messages.Add("Error: no PDF artifact was produced.")
}

$messages | Set-Content -Encoding UTF8 $Log
Write-Host "Wrote $Log"
Write-Host "Wrote $RepoPdf"
Write-Host "Copied to $DownloadPdf"
Write-Host "Copied to $DesktopPdf"
