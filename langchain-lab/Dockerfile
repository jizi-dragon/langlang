# 基础镜像：uv 官方提供的 Python 3.11 镜像（Bookworm / Debian 12）
# 同时包含 uv 包管理器，保证镜像内构建链路与生成 uv.lock 的链路完全一致
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# 非交互式安装，避免 apt 卡在时区等交互提示
ARG DEBIAN_FRONTEND=noninteractive

# 依赖缓存落后于代码，先拷贝锁文件以获得层缓存
WORKDIR /opt/lab
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 创建非 root 用户，避免以 root 运行学习脚本
RUN useradd -m -u 1000 learner

# 代码与数据挂载点：归 learner 所有，保证 SQLite checkpoint 等可写
RUN mkdir -p /workspace && chown learner:learner /workspace
WORKDIR /workspace

# 学习代码由宿主机挂载到 /workspace，镜像只锁定运行时与依赖，代码归属 Git 仓库
ENV PATH="/opt/lab/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

CMD ["python"]