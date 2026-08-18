# 快捷进入 langchain-lab 常驻容器（不存在则自动创建），实现"进容器后直接 python"
#
# 用法（在 langchain-lab 目录下运行）：
#   .\dev.ps1                     # 进入容器交互 shell
#   .\dev.ps1 examples\agent.py   # 在容器内运行某脚本

param(
    [string]$Entry = ""
)

$ErrorActionPreference = "Stop"
$image = "langchain-lab:3.11"
$name = "langlab"
$workdir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 镜像缺失时先构建，保证后续命令可执行
if (-not (docker images -q $image)) {
    Write-Host "[dev] 镜像 $image 不存在，先执行 rebuild.ps1 构建" -ForegroundColor Yellow
    & (Join-Path $workdir "rebuild.ps1")
}

$exists = docker ps -a --filter "name=^$name$" --format "{{.Names}}" | Select-Object -First 1
if (-not $exists) {
    Write-Host "[dev] 创建常驻容器 $name ..." -ForegroundColor Cyan
    $envArgs = @()
    if (Test-Path (Join-Path $workdir ".env")) {
        $envArgs = @("--env-file", (Join-Path $workdir ".env"))
    }
    docker run -d --name $name -v "${workdir}:/workspace" @envArgs -w /workspace $image sleep infinity | Out-Null
}
elseif ((docker inspect -f "{{.State.Running}}" $name) -ne "true") {
    Write-Host "[dev] 启动已存在的容器 $name ..." -ForegroundColor Cyan
    docker start $name | Out-Null
}

if ($Entry) {
    $Entry = $Entry -replace '\\', '/'
    docker exec $name python "/workspace/$Entry"
}
else {
    Write-Host "[dev] 已进入容器 $name，直接使用 python 命令即可" -ForegroundColor Green
    docker exec -it $name bash
}
