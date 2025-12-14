<# find-large-files.ps1 #>
# Finds the largest files in the project directory, excluding common dev/build folders.
# Adjust the minimum size (in MB) and the number of results to display.

$MinSizeMB = 1
$TopResults = 10
$ExcludePaths = @(
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    "venv_dev",
    "venv_runtime"
)

Write-Host "Searching for top $TopResults files larger than $MinSizeMB MB..."

# Build the filter string for Get-ChildItem to exclude directories
$ExcludeFilter = $ExcludePaths | ForEach-Object { "-and `$_.FullName -notlike '*\$_*'" }
$FilterString = "$ExcludeFilter" -join ' '

# Use a ScriptBlock with Get-ChildItem to evaluate the filter
Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { ($_.Length -gt ($MinSizeMB * 1MB)) -and (Invoke-Expression "`$True $FilterString") } |
    Select-Object -Property @{Name='Size (MB)'; Expression={'{0:N2}' -f ($_.Length / 1MB)}}, FullName |
    Sort-Object -Property 'Size (MB)' -Descending |
    Select-Object -First $TopResults |
    Format-Table -AutoSize

Write-Host "`nSearch complete."