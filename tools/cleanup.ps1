<# cleanup.ps1 #>
# Cleans up all Cleanup Build/Temporary Files
$CleanPaths = @(
    "dist",
    "build",
    "*.egg-info",
    "**\__pycache__", # Use Get-ChildItem -Recurse if not relying on shell expansion
    ".pytest_cache"
)

Write-Host "Removing temporary and build files..."
$CleanPaths | ForEach-Object {
    # Using -Force and -ErrorAction SilentlyContinue for robustness
    Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed: $_"
}