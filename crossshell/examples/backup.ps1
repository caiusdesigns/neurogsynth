[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $SourceDirectory = './data',

    [Parameter(Position = 1)]
    [string] $Destination = './archives'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $sourcePath = (Resolve-Path -LiteralPath $SourceDirectory).Path
    $destinationPath = [System.IO.Path]::GetFullPath($Destination)
    [System.IO.Directory]::CreateDirectory($destinationPath) | Out-Null

    $timestamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
    $archive = Join-Path $destinationPath "backup-$timestamp.zip"

    $files = Get-ChildItem -LiteralPath $sourcePath -File -Recurse |
        Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' }

    if (-not $files) {
        throw "No files found under $sourcePath"
    }

    # Compress-Archive accepts paths, not objects. Passing FullName explicitly
    # also avoids relying on the caller's current working directory.
    Compress-Archive -LiteralPath $files.FullName -DestinationPath $archive
    Write-Output "Created $archive"
}
catch {
    Write-Error "Backup failed: $($_.Exception.Message)"
    exit 1
}

