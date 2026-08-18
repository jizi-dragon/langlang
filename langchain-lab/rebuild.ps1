# 重建 langchain-lab 镜像（Windows / PowerShell）
# 升级依赖或改 Dockerfile 后需重新构建

$workdir = Split-Path -Parent $MyInvocation.MyCommand.Path
docker build -t langchain-lab:3.11 -f (Join-Path $workdir "Dockerfile") $workdir