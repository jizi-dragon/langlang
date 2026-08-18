# 启动 langchain-lab 学习环境（Windows / PowerShell）
#
# 用法（在 langchain-lab 目录下运行）：
#   .\run.ps1                     # 进入容器内交互式 python
#   .\run.ps1 examples\demo.py    # 在容器内运行某个脚本
#
# 依赖：本地已构建镜像 langchain-lab:3.11（或先运行 rebuild.ps1）

param(
    [string]$Entry = ""
)

$image = "langchain-lab:3.11"
$workdir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 环境变量注入：宿主 .env 存在则透传给容器
$envArgs = @()
if (Test-Path (Join-Path $workdir ".env")) {
    $envArgs = @("--env-file", (Join-Path $workdir ".env"))
}

$mount = "${workdir}:/workspace"

if ($Entry) {
    # 运行单个脚本（挂载整个项目，以便脚本内相对路径访问 data/ 等）
    # 将 Windows 反斜杠归一化为容器可识别的正斜杠
    $Entry = $Entry -replace '\\', '/'
    docker run --rm -v $mount @envArgs -w /workspace $image python $Entry
} else {
    # 交互式 python / ipython 环境
    docker run --rm -it -v $mount @envArgs -w /workspace $image python
}