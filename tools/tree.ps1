<# tree.ps1 #>
# Prints the Tree Structure of the Dev File Tree
$ExcludeList = "venv_dev", "venv_runtime", "__pycache__", ".pytest_cache", "documentation", "projects"
$DepthValue = 5

Write-Host "Running Command: PSTree -Exclude '$($ExcludeList -join ', ')' -Depth $DepthValue"

# Execute PSTree directly, passing the parameters
PSTree -Exclude $ExcludeList -Depth $DepthValue