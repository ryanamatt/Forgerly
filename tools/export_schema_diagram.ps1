<# export_schema_diagram.ps1 #>
# Parses schema_v1.sql and generates a Mermaid.js ER/Class diagram string.
# The output can be pasted into any Markdown file (like SCHEMA.md) inside a ```mermaid block.

$SchemaPath = Join-Path $PSScriptRoot "..\src\sql\schema_v1.sql"
$OutputPath = Join-Path $PSScriptRoot "..\docs\development\architecture\database_diagram.md"

if (-not (Test-Path $SchemaPath)) {
    Write-Error "Could not find schema file at $SchemaPath"
    exit
}

Write-Host "Reading schema from $SchemaPath..."
$Lines = Get-Content $SchemaPath

$Tables = @()
$CurrentTable = $null

# --- Basic Parser Logic ---
foreach ($Line in $Lines) {
    $TrimmedLine = $Line.Trim()
    
    # Identify Table Starts - FIXED: Account for "IF NOT EXISTS"
    if ($TrimmedLine -match "CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)") {
        $TableName = $Matches[1]
        $CurrentTable = @{
            Name = $TableName
            Columns = @()
            Relations = @()
        }
    }
    # Identify Columns and Foreign Keys
    elseif ($CurrentTable -ne $null) {
        if ($TrimmedLine -match "^\);") {
            $Tables += $CurrentTable
            $CurrentTable = $null
        }
        elseif ($TrimmedLine -match "FOREIGN KEY\s*\((.+?)\)\s*REFERENCES\s+(\w+)\s*\((.+?)\)") {
            $LocalCol = $Matches[1].Trim()
            $RemoteTable = $Matches[2].Trim()
            $CurrentTable.Relations += @{
                From = $CurrentTable.Name
                To = $RemoteTable
                Label = $LocalCol
            }
        }
        elseif ($TrimmedLine -match "^(\w+)\s+(\w+)") {
            $ColName = $Matches[1]
            $ColType = $Matches[2]
            # Exclude keywords like PRIMARY or FOREIGN
            if ($ColName -notmatch "PRIMARY|FOREIGN|CONSTRAINT|CHECK|UNIQUE") {
                $CurrentTable.Columns += "$ColType $ColName"
            }
        }
    }
}

# --- Generate Mermaid Output ---
$Mermaid = @("classDiagram", "    direction LR")

foreach ($Table in $Tables) {
    $Mermaid += "    class $($Table.Name) {"
    foreach ($Col in $Table.Columns) {
        $Mermaid += "        $Col"
    }
    $Mermaid += "    }"
}

# Add relationships after all classes are defined
foreach ($Table in $Tables) {
    foreach ($Rel in $Table.Relations) {
        # Using composition arrow to represent ownership/FK link
        $Mermaid += "    $($Rel.To) --* $($Rel.From) : $($Rel.Label)"
    }
}

$FinalDoc = @"
# Database Schema Diagram

*Generated automatically from src/sql/schema_v1.sql*

``````mermaid
$($Mermaid -join "`n")
``````
"@

$FinalDoc | Out-File -FilePath $OutputPath -Encoding utf8
Write-Host "✅ Diagram generated successfully at $OutputPath"
Write-Host "You can view this in GitHub or any Mermaid-compatible Markdown previewer."