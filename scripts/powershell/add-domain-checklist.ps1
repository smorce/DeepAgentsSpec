#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$FeatureId,
    [Parameter(Mandatory = $true)]
    [string]$Template,
    [string]$Output,
    [string[]]$Service,
    [string]$Search,
    [switch]$Force,
    [switch]$List,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..' '..')).Path
$templateDir = Join-Path $repoRoot 'templates/checklist'

function Show-Usage {
    Write-Output @" 
Usage: add-domain-checklist.ps1 -Template <name> [options]

Options:
  -FeatureId <ID>   Feature ID in harness/feature_list.json (defaults to SPECIFY_FEATURE)
  -Template <name>  Template filename or slug under templates/checklist (required)
  -Output <name>    Destination filename (default: <template-slug>.md)
  -Service <name>   Filter feature lookup by owning service (repeatable)
  -Search <text>    Filter feature lookup by substring in ID/title
  -Force            Overwrite destination file if it exists
  -List             Show available templates and exit
  -Json             Emit machine-readable output
  -Help             Show this help message

Example:
  scripts/powershell/add-domain-checklist.ps1 -FeatureId F-API-001 -Template "統合セキュリティガイドライン チェックリスト"
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

if ($List) {
    Write-Output 'Available templates:'
    Get-ChildItem -Path $templateDir -Filter '*.md' | Sort-Object Name | ForEach-Object {
        Write-Output ('  - {0}' -f $_.Name)
    }
    exit 0
}

if (-not $Template) {
    Write-Error 'Error: -Template is required'
    exit 1
}

if (-not $FeatureId) {
    if ($env:SPECIFY_FEATURE -and $env:SPECIFY_FEATURE -match '^F-[A-Za-z0-9-]+$') {
        $FeatureId = $env:SPECIFY_FEATURE
    }
}

if (-not $FeatureId) {
    Write-Error 'Error: -FeatureId is required (or set SPECIFY_FEATURE)'
    exit 1
}

$FeatureId = $FeatureId.ToUpper()

function Load-FeatureList {
    param([string]$Path)
    $content = Get-Content $Path
    $filtered = $content | Where-Object { $_ -notmatch '^\s*//' }
    return ($filtered -join "`n") | ConvertFrom-Json
}

$harnessFile = Join-Path $repoRoot 'harness/feature_list.json'
if (-not (Test-Path $harnessFile -PathType Leaf)) {
    Write-Error "File not found: $harnessFile"
    exit 1
}
$featureData = Load-FeatureList -Path $harnessFile

function Get-FeatureMetadata {
    param([object]$FeatureData, [string]$RepoRoot, [string]$TargetId)
    $match = $FeatureData.features | Where-Object { $_.id.ToUpper() -eq $TargetId }
    if (-not $match) {
        throw "Feature ID $TargetId not found in harness/feature_list.json"
    }
    $specRel = $match.spec_path
    if (-not $specRel) { throw "Feature ID $TargetId is missing spec_path" }
    $specPathCandidate = Join-Path $RepoRoot $specRel
    if (Test-Path $specPathCandidate) {
        $specPath = (Resolve-Path $specPathCandidate).Path
    } else {
        $specPath = [System.IO.Path]::GetFullPath($specPathCandidate)
    }
    return [PSCustomObject]@{
        FeatureDir   = (Split-Path $specPath -Parent)
        FeatureTitle = if ($match.title) { $match.title } else { $TargetId }
    }
}

function Find-TemplatePath {
    param([string]$TemplateDir, [string]$Key)
    if (Test-Path $Key -PathType Leaf) { return (Resolve-Path $Key).Path }
    $candidate = Join-Path $TemplateDir $Key
    if (Test-Path $candidate -PathType Leaf) { return (Resolve-Path $candidate).Path }
    $normalized = $Key.ToLower()
    $match = Get-ChildItem -Path $TemplateDir -Filter '*.md' | Where-Object { $_.Name.ToLower().Contains($normalized) } | Select-Object -First 1
    if ($match) { return $match.FullName }
    return $null
}

$templatePath = Find-TemplatePath -TemplateDir $templateDir -Key $Template
if (-not $templatePath) {
    Write-Error "Template '$Template' not found under $templateDir"
    exit 1
}

try {
    $meta = Get-FeatureMetadata -FeatureData $featureData -RepoRoot $repoRoot -TargetId $FeatureId
} catch {
    Write-Error $_.Exception.Message
    exit 1
}

$destDir = Join-Path $meta.FeatureDir 'checklists'
New-Item -ItemType Directory -Path $destDir -Force | Out-Null

if (-not $Output) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($templatePath)
    $Output = "$base.md"
}
if (-not $Output.EndsWith('.md')) { $Output += '.md' }
$destPath = Join-Path $destDir $Output

if ((Test-Path $destPath -PathType Leaf) -and (-not $Force)) {
    Write-Error "File already exists: $destPath (use -Force to overwrite)"
    exit 1
}

Copy-Item -Path $templatePath -Destination $destPath -Force

$dateStamp = Get-Date -Format 'yyyy-MM-dd'
$content = Get-Content $destPath -Raw
$content = $content.Replace('[FEATURE NAME]', $meta.FeatureTitle)
$content = $content.Replace('[FEATURE-ID]', $FeatureId)
$content = $content.Replace('[DATE]', $dateStamp)
Set-Content -Path $destPath -Value $content -Encoding UTF8

if ($Json) {
    [PSCustomObject]@{
        feature_id = $FeatureId
        template   = $templatePath
        output     = $destPath
    } | ConvertTo-Json -Compress
} else {
    Write-Output "Checklist created:"
    Write-Output "  Feature ID : $FeatureId"
    Write-Output "  Template   : $templatePath"
    Write-Output "  Output     : $destPath"
}
