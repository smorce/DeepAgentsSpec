#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$FeatureId,
    [string]$ShortName,
    [string[]]$Service,
    [string]$Search,
    [switch]$Json,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @" 
Usage: create-new-feature.ps1 -FeatureId F-XXX-YYY [options] <feature description>

Options:
  -FeatureId <ID>   Target feature ID defined in harness/feature_list.json (required)
  -ShortName <slug> Optional short slug for branch naming
  -Service <name>   Filter candidate features by owning service (repeatable)
  -Search <text>    Filter candidate features by substring in ID/title
  -Json             Emit machine-readable JSON
  -Help             Show this help message
"@
    exit 0
}

$repoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$featureDesc = ($FeatureDescription -join ' ').Trim()

if (-not $FeatureId) {
    if ($env:SPECIFY_FEATURE -and $env:SPECIFY_FEATURE -match '^F-[A-Za-z0-9-]+$') {
        $FeatureId = $env:SPECIFY_FEATURE
    } else {
        $matches = Find-FeaturesByFilter -FeatureData $featureData -Services $Service -SearchTerm $Search
        if ($matches.Count -eq 0) {
            Write-Error "No feature matches filters. Provide -FeatureId or use -Service/-Search to narrow."
            exit 1
        }
        if ($matches.Count -gt 1) {
            Write-Error "Multiple features match filters. Use -FeatureId to disambiguate. Candidates:"
            foreach ($m in $matches) {
                Write-Error ("  - {0} | {1} | {2}" -f $m.Id, $m.Title, $m.Services)
            }
            exit 1
        }
        $FeatureId = $matches[0].Id
    }
}

$featureId = $FeatureId.ToUpper()

$harnessFile = Join-Path $repoRoot 'harness/feature_list.json'
if (-not (Test-Path $harnessFile -PathType Leaf)) {
    Write-Error "File not found: $harnessFile"
    exit 1
}

function Load-FeatureList {
    param([string]$HarnessPath)
    $content = Get-Content $HarnessPath
    $filtered = $content | Where-Object { $_ -notmatch '^\s*//' }
    return ($filtered -join "`n") | ConvertFrom-Json
}

$featureData = Load-FeatureList -HarnessPath $harnessFile

function Get-FeatureMetadata {
    param(
        [object]$FeatureData,
        [string]$RepoRoot,
        [string]$TargetId
    )

    $match = $FeatureData.features | Where-Object { $_.id.ToUpper() -eq $TargetId }
    if (-not $match) {
        throw "Feature ID $TargetId not found in harness/feature_list.json"
    }

    $specRel = $match.spec_path
    if (-not $specRel) {
        throw "Feature ID $TargetId is missing spec_path in harness/feature_list.json"
    }

    $specPathCandidate = Join-Path $RepoRoot $specRel
    if (Test-Path $specPathCandidate) {
        $specPath = (Resolve-Path $specPathCandidate).Path
    } else {
        $specPath = [System.IO.Path]::GetFullPath($specPathCandidate)
    }
    $defaultChecklist = Join-Path (Split-Path $specRel -Parent) 'checklists/requirements.md'
    $checklistRel = if ($match.checklist_path) { $match.checklist_path } else { $defaultChecklist }
    $checklistCandidate = Join-Path $RepoRoot $checklistRel
    if (Test-Path $checklistCandidate) {
        $checklistPath = (Resolve-Path $checklistCandidate).Path
    } else {
        $checklistPath = [System.IO.Path]::GetFullPath($checklistCandidate)
    }

    return [PSCustomObject]@{
        SpecPath      = $specPath
        ChecklistPath = $checklistPath
        FeatureTitle  = if ($match.title) { $match.title } else { $TargetId }
        Services      = ($match.services -join ',')
        EpicId        = $match.epic_id
    }
}

function Find-FeaturesByFilter {
    param(
        [object]$FeatureData,
        [string[]]$Services,
        [string]$SearchTerm
    )

    $serviceFilters = @()
    if ($Services) {
        $serviceFilters = $Services | Where-Object { $_ } | ForEach-Object { $_.ToLower() }
    }
    $term = if ($SearchTerm) { $SearchTerm.ToLower() } else { '' }

    $matches = @()
    foreach ($feat in $FeatureData.features) {
        $fid = [string]$feat.id
        $title = [string]($feat.title)
        $svcList = @()
        if ($feat.services) { $svcList = $feat.services | ForEach-Object { $_.ToLower() } }

        if ($serviceFilters.Count -gt 0 -and (-not ($svcList | Where-Object { $serviceFilters -contains $_ }))) {
            continue
        }

        if ($term) {
            $hay = "{0} {1}" -f $fid, $title
            if ($hay.ToLower().IndexOf($term) -lt 0) { continue }
        }

        $matches += [PSCustomObject]@{
            Id        = $fid
            Title     = $title
            Services  = ($feat.services -join ',')
            SpecPath  = $feat.spec_path
        }
    }
    return $matches
}

try {
    $meta = Get-FeatureMetadata -FeatureData $featureData -RepoRoot $repoRoot -TargetId $featureId
} catch {
    Write-Error $_.Exception.Message
    exit 1
}

$featureDir    = Split-Path $meta.SpecPath -Parent
$checklistDir  = Split-Path $meta.ChecklistPath -Parent
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null
New-Item -ItemType Directory -Path $checklistDir -Force | Out-Null

function Invoke-Slugify([string]$Value) {
    if (-not $Value) { return "" }
    $Value.ToLower() -replace '[^a-z0-9]+', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

$branchPrefix = ""
if ($featureId -match '([0-9]{3,})$') {
    $branchPrefix = $matches[1]
}

if ($ShortName) {
    $branchSuffix = Invoke-Slugify $ShortName
} elseif ($featureDesc) {
    $branchSuffix = Invoke-Slugify $featureDesc
} else {
    $branchSuffix = Invoke-Slugify $meta.FeatureTitle
}
if (-not $branchSuffix) { $branchSuffix = "feature" }

if ($branchPrefix) {
    $branchName = "$branchPrefix-$branchSuffix"
} else {
    $branchName = ("{0}-{1}" -f $featureId.ToLower(), $branchSuffix)
}
if ($branchName.Length -gt 244) {
    $branchName = $branchName.Substring(0, 244).TrimEnd('-')
}

$hasGit = $false
try {
    git -C $repoRoot rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
        Set-Location $repoRoot
        if (git rev-parse --verify "refs/heads/$branchName" 2>$null) {
            git checkout $branchName 2>$null | Out-Null
        } else {
            git checkout -b $branchName 2>$null | Out-Null
        }
    }
} catch {
    Write-Warning "[create-new-feature] Git repository not detected; branch creation skipped."
}

$dateStamp = (Get-Date -Format 'yyyy-MM-dd')
$descText = if ($featureDesc) { $featureDesc } else { "Feature description not provided" }

$specTemplate = Join-Path $repoRoot 'templates/spec-template.md'
if (-not (Test-Path $meta.SpecPath -PathType Leaf)) {
    if (Test-Path $specTemplate -PathType Leaf) {
        Copy-Item $specTemplate $meta.SpecPath
    } else {
        '# Feature Specification' | Set-Content $meta.SpecPath -Encoding UTF8
    }
    $content = Get-Content $meta.SpecPath -Raw
    $content = $content.Replace('[FEATURE NAME]', $meta.FeatureTitle, 1)
    $content = $content.Replace('[F-XXX-YYY]', $featureId, 1)
    $content = $content.Replace('[###-feature-name]', $branchName, 1)
    $content = $content.Replace('[DATE]', $dateStamp, 1)
    $content = $content.Replace('$ARGUMENTS', $descText, 1)
    Set-Content -Path $meta.SpecPath -Value $content -Encoding UTF8
} else {
    Write-Warning "[create-new-feature] Spec already exists at $($meta.SpecPath); leaving untouched."
}

if (-not (Test-Path $meta.ChecklistPath -PathType Leaf)) {
    @"
# ${featureId} Requirements Checklist

**Created**: ${dateStamp}
**Feature**: ${meta.FeatureTitle}

## Content Quality
- [ ] No [NEEDS CLARIFICATION] markers remain in spec.md
- [ ] Requirements are testable and free from implementation details
- [ ] Scope boundaries and success criteria are clearly written

## Acceptance Readiness
- [ ] User stories have measurable acceptance scenarios
- [ ] Edge cases and error states are captured in the specification
- [ ] Dependencies and assumptions are documented
"@ | Set-Content -Path $meta.ChecklistPath -Encoding UTF8
} else {
    Write-Warning "[create-new-feature] Checklist already exists at $($meta.ChecklistPath); leaving untouched."
}

$env:SPECIFY_FEATURE = $featureId

$result = [PSCustomObject]@{
    BRANCH_NAME    = $branchName
    SPEC_FILE      = $meta.SpecPath
    FEATURE_ID     = $featureId
    FEATURE_TITLE  = $meta.FeatureTitle
    FEATURE_DIR    = $featureDir
    CHECKLIST_FILE = $meta.ChecklistPath
    EPIC_ID        = $meta.EpicId
    SERVICES       = $meta.Services
}

if ($Json) {
    $result | ConvertTo-Json -Compress
} else {
    Write-Output ("Feature ID     : {0}" -f $featureId)
    Write-Output ("Spec file      : {0}" -f $meta.SpecPath)
    Write-Output ("Checklist file : {0}" -f $meta.ChecklistPath)
    Write-Output ("Feature dir    : {0}" -f $featureDir)
    Write-Output ("Branch name    : {0}" -f $branchName)
    Write-Output ("Epic ID        : {0}" -f ($meta.EpicId | ForEach-Object { if ($_){$_} else {'N/A'} }))
    Write-Output ("Services       : {0}" -f ($meta.Services | ForEach-Object { if ($_){$_} else {'N/A'} }))
    Write-Output ("SPECIFY_FEATURE environment variable set to: {0}" -f $featureId)
}
