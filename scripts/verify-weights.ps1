<#
  校验模型权重完整性（Windows PowerShell 5.1 兼容）

  两个检查：
    1. Git LFS 指针检测 —— 没装 git-lfs 或没执行 git lfs pull 时，权重文件只是约 130
       字节的文本指针（内容以 "version https://git-lfs" 开头）。此时文件"存在"但模型
       加载会失败，是最容易踩的坑。
    2. 按 backend/algorithm/weights.md5 逐个校验 MD5，检出损坏或串版本。

  用法（仓库根目录下）：
      powershell -ExecutionPolicy Bypass -File scripts\verify-weights.ps1
      powershell -ExecutionPolicy Bypass -File scripts\verify-weights.ps1 -Quiet

  退出码：0 = 全部正常；1 = 有问题（缺文件 / 是指针 / 校验不通过）
#>
param([switch]$Quiet)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$WeightsDir = Join-Path $Root 'backend\algorithm\weights'
$Manifest = Join-Path $Root 'backend\algorithm\weights.md5'

function Say($msg, $color) {
    if (-not $color) { $color = 'Gray' }
    if (-not $Quiet -or $color -eq 'Red' -or $color -eq 'Yellow') {
        Write-Host $msg -ForegroundColor $color
    }
}

if (-not (Test-Path $WeightsDir)) {
    Write-Host "[FAIL] 权重目录不存在：$WeightsDir" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $Manifest)) {
    Write-Host "[FAIL] 缺少清单文件：$Manifest" -ForegroundColor Red
    exit 1
}

# ---------- 1) LFS 指针检测 ----------
$pointers = @()
foreach ($f in Get-ChildItem $WeightsDir -Recurse -File) {
    if ($f.Length -gt 1024) { continue }
    $head = Get-Content $f.FullName -TotalCount 1 -ErrorAction SilentlyContinue
    if ($head -match '^version https://git-lfs') {
        $pointers += $f.FullName.Substring($WeightsDir.Length + 1)
    }
}
if ($pointers.Count -gt 0) {
    Write-Host "[FAIL] 检测到 $($pointers.Count) 个 Git LFS 指针文件，权重并未真正下载。" -ForegroundColor Red
    $pointers | Select-Object -First 5 | ForEach-Object { Write-Host "       $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  解决办法（二选一）：" -ForegroundColor Yellow
    Write-Host "    a) 安装 git-lfs（https://git-lfs.com/），装完重新打开终端，然后在仓库里执行："
    Write-Host "         git lfs install"
    Write-Host "         git lfs pull"
    Write-Host "    b) 本机无法使用 LFS 时：向平台方索取权重压缩包，解压到"
    Write-Host "       backend\algorithm\weights\ 覆盖后，重新运行本脚本校验。"
    exit 1
}

# ---------- 2) MD5 校验 ----------
$missing = @()
$mismatch = @()
$ok = 0
$total = 0

foreach ($line in Get-Content $Manifest) {
    if ($line -notmatch '^([0-9a-fA-F]{32})\s+(.+?)\s*$') { continue }
    $total++
    $expect = $Matches[1].ToLower()
    $rel = $Matches[2]
    $file = Join-Path $WeightsDir ($rel -replace '/', '\')

    if (-not (Test-Path $file)) { $missing += $rel; continue }

    $actual = (Get-FileHash $file -Algorithm MD5).Hash.ToLower()
    if ($actual -ne $expect) {
        $mismatch += [pscustomobject]@{ File = $rel; Expect = $expect; Actual = $actual }
    } else {
        $ok++
    }
}

$summaryColor = 'Green'
if ($missing.Count -gt 0 -or $mismatch.Count -gt 0) { $summaryColor = 'Yellow' }
Say ("权重校验：{0} / {1} 通过（{2}）" -f $ok, $total, $WeightsDir) $summaryColor

if ($missing.Count -gt 0) {
    Write-Host "[FAIL] 缺少 $($missing.Count) 个权重文件：" -ForegroundColor Red
    $missing | Select-Object -First 10 | ForEach-Object { Write-Host "       $_" -ForegroundColor Red }
    exit 1
}
if ($mismatch.Count -gt 0) {
    Write-Host "[FAIL] $($mismatch.Count) 个权重文件 MD5 不符（文件损坏或版本串了）：" -ForegroundColor Red
    foreach ($m in ($mismatch | Select-Object -First 10)) {
        Write-Host "       $($m.File)" -ForegroundColor Red
        Write-Host "         期望 $($m.Expect)" -ForegroundColor DarkGray
        Write-Host "         实际 $($m.Actual)" -ForegroundColor DarkGray
    }
    exit 1
}

Say "所有权重完整、未被损坏 [OK]" 'Green'
exit 0
