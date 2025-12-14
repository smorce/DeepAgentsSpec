#!/usr/bin/env pwsh
# リポジトリ共通の PowerShell ユーティリティ

function Get-RepoRoot {
    if (git rev-parse --show-toplevel 2>$null) {
        return (git rev-parse --show-toplevel)
    }
    $scriptDir = Split-Path -Parent $PSCommandPath
    $rootCandidate = Resolve-Path (Join-Path $scriptDir "..\..") -ErrorAction SilentlyContinue
    if ($rootCandidate) { return $rootCandidate.Path }
    return (Get-Location).Path
}

function Get-CurrentBranch {
    if (git rev-parse --abbrev-ref HEAD 2>$null) {
        return (git rev-parse --abbrev-ref HEAD)
    }
    if ($env:SPECIFY_FEATURE) { return $env:SPECIFY_FEATURE }
    return "unknown"
}

function Test-HasGit {
    return (git rev-parse --show-toplevel 2>$null) -ne $null
}

function Get-FeatureHint {
    param([string]$Branch)

    if ($env:FEATURE_DIR) { return $env:FEATURE_DIR }
    if ($env:FEATURE_SPEC) { return (Split-Path -Parent $env:FEATURE_SPEC) }
    if ($env:FEATURE_ID) { return $env:FEATURE_ID }
    if ($env:SPECIFY_FEATURE) { return $env:SPECIFY_FEATURE }

    if ($Branch -match '(F-[A-Za-z0-9-]+)') {
        return $matches[1]
    }
    return ""
}

function Normalize-RepoPath {
    param(
        [string]$RepoRoot,
        [string]$Value,
        [switch]$AllowNonExisting
    )

    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $raw = $Value
    if (-not [System.IO.Path]::IsPathRooted($raw)) {
        $raw = Join-Path $RepoRoot $raw
    }

    try {
        if (Test-Path -LiteralPath $raw -PathType Any) {
            return (Resolve-Path -LiteralPath $raw).Path
        }
        if ($AllowNonExisting) {
            return [System.IO.Path]::GetFullPath($raw)
        }
    } catch {
        if ($AllowNonExisting) {
            return [System.IO.Path]::GetFullPath($raw)
        }
    }
    return ""
}

function Resolve-FeatureDirectory {
    param(
        [string]$RepoRoot,
        [string]$Hint
    )

    if ([string]::IsNullOrWhiteSpace($Hint)) { return "" }

    $candidate = Normalize-RepoPath -RepoRoot $RepoRoot -Value $Hint
    if ($candidate) {
        if (Test-Path -LiteralPath $candidate -PathType Container) { return $candidate }
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Split-Path -Parent $candidate) }
    }

    $looksLikePath = $Hint -match '^(?:\./|\.\./)?(plans|services)/'
    if ($looksLikePath) {
        $pathCandidate = Normalize-RepoPath -RepoRoot $RepoRoot -Value $Hint -AllowNonExisting
        if ($pathCandidate) {
            if ($pathCandidate.EndsWith(".md")) {
                return (Split-Path -Parent $pathCandidate)
            }
            return $pathCandidate
        }
    }

    if ($Hint -match '(F-[A-Za-z0-9-]+)') {
        $featureId = $matches[1].ToUpper()
        $featureList = Join-Path $RepoRoot "harness/feature_list.json"
        if (Test-Path $featureList -PathType Leaf) {
            try {
                $json = Get-Content $featureList -Raw | ConvertFrom-Json
                foreach ($feature in $json.features) {
                    if (($feature.id).ToUpper() -eq $featureId) {
                        $specPath = $feature.spec_path
                        if ($specPath) {
                            $dir = Normalize-RepoPath -RepoRoot $RepoRoot -Value (Split-Path -Parent $specPath) -AllowNonExisting
                            if ($dir) { return $dir }
                        }
                    }
                }
            } catch {
                # JSON が壊れている場合は検索継続
            }
        }
    }

    $plansRoot = Join-Path $RepoRoot "plans"
    if (Test-Path $plansRoot -PathType Container) {
        $match = Get-ChildItem -Path $plansRoot -Directory -Recurse |
            Where-Object { $_.Name -ieq $Hint } |
            Select-Object -First 1
        if ($match) { return $match.FullName }
    }

    return ""
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )

    if (-not $HasGit) {
        Write-Warning "[specify] Git が見つからなかったため、ブランチ名の検証をスキップしました。"
        return $true
    }

    if ($Branch -in @("main", "master")) {
        Write-Output "ERROR: 作業用の feature ブランチに切り替えてください。現在: $Branch"
        return $false
    }

    if ($Branch -match '^[0-9]{3}-' -or $Branch -match 'F-[A-Za-z0-9-]+') {
        return $true
    }

    Write-Output "ERROR: フィーチャーブランチ形式を検出できませんでした (例: 004-new-flow / F-USER-001-impl)。"
    return $false
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $branch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $hint = Get-FeatureHint -Branch $branch

    if (-not $hint) {
        throw "フィーチャーのヒントを特定できませんでした。FEATURE_ID もしくは SPECIFY_FEATURE を設定してください。"
    }

    $featureDir = Resolve-FeatureDirectory -RepoRoot $repoRoot -Hint $hint
    if (-not $featureDir) {
        throw "ヒント '$hint' に対応するフィーチャーディレクトリを解決できませんでした。"
    }

    return [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $branch
        HAS_GIT        = $hasGit
        FEATURE_DIR    = $featureDir
        FEATURE_ID     = Split-Path $featureDir -Leaf
        FEATURE_SPEC   = Join-Path $featureDir 'spec.md'
        IMPL_PLAN      = Join-Path $featureDir 'impl-plan.md'
        TASKS          = Join-Path $featureDir 'tasks.md'
        RESEARCH       = Join-Path $featureDir 'research.md'
        DATA_MODEL     = Join-Path $featureDir 'data-model.md'
        QUICKSTART     = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR  = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and
        (Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}
