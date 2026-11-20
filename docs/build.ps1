[CmdletBinding()] param (
    [string[]]$docfxArgs
)
Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

Push-Location $PSScriptRoot
try {
    if (Test-Path "..\artifacts\docs") {
        Remove-Item "..\artifacts\docs\*" -Recurse -Force
    }

    uv run ..\.github\workflows\gen-whoami-table.py ..\whoami.yml ..\artifacts\docs\whoami.md
    dotnet docfx build $docfxArgs
} finally {
    Pop-Location
}
