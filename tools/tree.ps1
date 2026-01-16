<# tree.ps1 #>
# Prints the Tree Structure of the Dev File Tree
$ExcludeList = "venv", "__pycache__", ".pytest_cache", "api", "projects", "resources", "dist", "build"
$DepthValue = 5

Write-Host "Running Command: PSTree -Exclude '$($ExcludeList -join ', ')' -Depth $DepthValue"

# Execute PSTree directly, passing the parameters
PSTree -Exclude $ExcludeList -Depth $DepthValue