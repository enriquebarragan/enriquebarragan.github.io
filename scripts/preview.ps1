Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting local Jekyll preview..."
Write-Host "Open http://localhost:4000 when the server is ready."
Write-Host "Press Ctrl+C here to stop the preview."

docker run --rm -it `
  -p 4000:4000 `
  -v "${repoRoot}:/site" `
  -w /site `
  ruby:3.2 `
  bash -lc "bundle install && bundle exec jekyll serve --host 0.0.0.0 --livereload --force_polling"
