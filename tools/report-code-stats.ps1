<# report-code-stats.ps1 #>
# Calculates and reports the Lines of Code (LOC) for Python, C++, and SQL files.
$SourcePath = ".\src"

# Filter out the generated resource file to keep stats accurate
$PythonFiles = Get-ChildItem -Path $SourcePath -Filter "*.py" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne "resources_rc.py" }

$CSourceFiles = Get-ChildItem -Path "$SourcePath\c_lib" -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -eq ".cpp" -or $_.Extension -eq ".h" }

# New: Collect SQL files
$SqlFiles = Get-ChildItem -Path "$SourcePath\sql" -Filter "*.sql" -Recurse -ErrorAction SilentlyContinue

function Get-LOC ($File) {
    # Count non-empty, non-comment lines
    (Get-Content -Path $File | Where-Object {
        $_.Trim() -ne "" -and # Ignore empty lines
        $_.Trim() -notlike "#*" -and # Ignore Python comments
        $_.Trim() -notlike "//*" -and # Ignore C++ single-line comments
        $_.Trim() -notlike "--*" # Ignore SQL comments
    }).Count
}

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

# New: SQL Statistics Section
Write-Host "`n--- SQL Code Statistics (./src/sql) ---"
$SqlStats = $SqlFiles | Select-Object -Property Name, @{Name='LOC'; Expression={Get-LOC $_.FullName}}
$SqlStats | Format-Table -AutoSize
$SqlTotal = ($SqlStats | Measure-Object -Property LOC -Sum).Sum
Write-Host "Total SQL LOC: $SqlTotal"

$GrandTotal = $PythonTotal + $CTotal + $SqlTotal
Write-Host "`n--- Grand Total LOC: $GrandTotal ---"