<# report-code-stats.ps1 #>
# Calculates and reports the Lines of Code (LOC) for Python and C files.
$SourcePath = ".\src"
$PythonFiles = Get-ChildItem -Path $SourcePath -Filter "*.py" -Recurse -ErrorAction SilentlyContinue

# FIX: Use Where-Object to filter for multiple extensions, as -Filter only accepts a single string.
$CSourceFiles = Get-ChildItem -Path "$SourcePath\c_lib" -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -eq ".cpp" -or $_.Extension -eq ".h" }

function Get-LOC ($File) {
    # Count non-empty, non-comment lines
    (Get-Content -Path $File | Where-Object {
        $_.Trim() -ne "" -and # Ignore empty lines
        $_.Trim() -notlike "#*" -and # Ignore Python comments
        $_.Trim() -notlike "//*" # Ignore C++ single-line comments
    }).Count
}

$TotalLOC = 0

Write-Host "--- Python Code Statistics (./src/python) ---"
$PythonStats = $PythonFiles | Select-Object -Property Name, @{Name='LOC'; Expression={Get-LOC $_.FullName}}
$PythonStats | Format-Table -AutoSize
$PythonTotal = ($PythonStats | Measure-Object -Property LOC -Sum).Sum
Write-Host "Total Python LOC: $PythonTotal"

Write-Host "`n--- C/C++ Code Statistics (./src/c_lib) ---"
$CStats = $CSourceFiles | Select-Object -Property Name, @{Name='LOC'; Expression={Get-LOC $_.FullName}}
$CStats | Format-Table -AutoSize
$CTotal = ($CStats | Measure-Object -Property LOC -Sum).Sum
Write-Host "Total C/C++ LOC: $CTotal"

$GrandTotal = $PythonTotal + $CTotal
Write-Host "`n--- Grand Total LOC: $GrandTotal ---"