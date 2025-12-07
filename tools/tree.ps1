$Command = PSTree -Exclude "venv_dev", "venv_runtime", "__pycache__", ".pytest_cache", "documentation"  -Depth 5

Write-Host "Running Command: $Command"

Invoke-Expression $Command