#!/usr/bin/env pwsh
<#
.SYNOPSIS
  把已安装的 Claude Code skill（~/.claude/skills/qigua/SKILL.md）一键同步进本仓库的
  claude-skill/SKILL.md，可选一并 commit + push。

.DESCRIPTION
  方向：installed -> repo（已安装那份是你日常用 /skill-tuner 等迭代的"源"）。
  幂等：内容一致时直接跳过，不产生空提交。

  注意：DeepSeek 模式的 deepseek-mode/SYSTEM_PROMPT.md 是独立手写文件、格式不同，
  【不在本脚本同步范围】。若你改的是"解卦方法论"本身，记得手动把对应改动也落到
  SYSTEM_PROMPT.md，否则两套模式会逐渐漂移。

.EXAMPLE
  ./sync-skill.ps1
  # 只同步并显示差异，不推送

.EXAMPLE
  ./sync-skill.ps1 -Push -Message "解卦：补纳甲法"
  # 同步并自动 commit & push
#>
param(
    [switch]$Push,
    [string]$Message = "sync: 同步 Claude skill SKILL.md"
)

$ErrorActionPreference = "Stop"

$src = Join-Path $env:USERPROFILE ".claude\skills\qigua\SKILL.md"
$dst = Join-Path $PSScriptRoot "claude-skill\SKILL.md"

if (-not (Test-Path $src)) {
    Write-Host "✗ 找不到已安装的 skill：$src" -ForegroundColor Red
    exit 1
}

if ((Test-Path $dst) -and ((Get-FileHash $src).Hash -eq (Get-FileHash $dst).Hash)) {
    Write-Host "✓ 仓库副本已是最新，无需同步。" -ForegroundColor Green
    exit 0
}

Copy-Item $src $dst -Force
Write-Host "✓ 已同步：~/.claude/skills/qigua/SKILL.md -> claude-skill/SKILL.md" -ForegroundColor Green
Write-Host "  提醒：DeepSeek 版 SYSTEM_PROMPT.md 不随此脚本同步，方法论若变需手动跟进。" -ForegroundColor Yellow

Push-Location $PSScriptRoot
try {
    git add claude-skill/SKILL.md | Out-Null
    Write-Host "`n本次改动："
    git --no-pager diff --cached --stat

    if ($Push) {
        git commit -q -m $Message
        git push
        Write-Host "✓ 已 commit 并 push。" -ForegroundColor Green
    } else {
        Write-Host "`n未推送。要推送：./sync-skill.ps1 -Push   或手动 git commit/push。" -ForegroundColor Cyan
    }
} finally {
    Pop-Location
}
