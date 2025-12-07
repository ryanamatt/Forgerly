$ExcludeList = "venv_dev", "venv_runtime", "__pycache__", ".pytest_cache", "documentation"
$DepthValue = 5

Write-Host "Running Command: PSTree -Exclude '$($ExcludeList -join ', ')' -Depth $DepthValue"

# Execute PSTree directly, passing the parameters
PSTree -Exclude $ExcludeList -Depth $DepthValue