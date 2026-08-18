# langchain-lab

面向 LangChain / LangGraph 学习的 Docker 开发环境（**Python 3.11**，单镜像），用于在**多台电脑间保持环境一致**。

## 目录结构

```
langchain-lab/
├── Dockerfile          # 镜像定义（uv + python3.11-slim）
├── pyproject.toml      # 依赖声明（版本区间）
├── uv.lock             # 锁定精确版本（跨机一致性关键）
├── .env.example        # 环境变量模板（复制为 .env 使用）
├── .env                # 你的 API Key（不入库）
├── .gitignore
├── .dockerignore
├── run.ps1             # 运行脚本
├── rebuild.ps1         # 重建镜像
└── examples/
    ├── smoke_test.py   # 离线冒烟测试（无需 Key）
    └── demo.py         # langchain-openai 调用示例（需 Key）
```

## 职责边界（务必理解）

- **镜像**只负责锁定**运行时与依赖**；**代码**归属 **Git 仓库**，经 `-v` 挂载进容器。
- 这套设计的写照是：`Dockerfile + uv.lock + Git 仓库` 三者共同保证两台电脑一致，**单 pull 一个镜像并不保证代码一致**。
- 容器使用 root 运行（学习环境、容器随用随毁），以避开 Windows 宿主目录挂载的 uid 权限问题。

## 首次使用（每台电脑都做一次）

### 1. 构建镜像

```powershell
.\rebuild.ps1
```

### 2. 配置 API Key

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填入你的 OpenAI 兼容服务商信息（DeepSeek / 通义 / Kimi 等均适用）。

### 3. 运行

离线验证依赖装到位：

```powershell
.\run.ps1 examples/smoke_test.py
```

调用真实 LLM：

```powershell
.\run.ps1 examples/demo.py
```

进入交互式 Python（便于逐步学习、试验图结构）：

```powershell
.\run.ps1
```

## 两台电脑的一致性保证

1. 本项目（含 `uv.lock`、`Dockerfile`、`examples/`）纳入 Git 仓库。
2. 换机器时 `git clone` 到同样的路径，执行 `.\rebuild.ps1` 生成**完全一致**的镜像与依赖版本。
3. `.env` 不入库，各自机器维护自己的 Key；代码与依赖保持一致。

## 依赖清单

由 `uv.lock` 锁定（首次生成时的主要版本）：

- langchain / langchain-core / langchain-openai
- langgraph / langgraph-checkpoint-sqlite / langgraph-cli / langgraph-prebuilt / langgraph-sdk
- langsmith（可观测性）、python-dotenv

## 添加 / 升级依赖

编辑 `pyproject.toml` 中的 `dependencies`，然后重新生成锁文件（在容器内执行，保证针对 Python 3.11）：

```powershell
docker run --rm -v "${PWD}:/work" -w /work ghcr.io/astral-sh/uv:python3.11-bookworm-slim uv lock
.\rebuild.ps1
```

> 提示：国内网络下可通过设置 `UV_DEFAULT_INDEX` 指向镜像源加速，具体见 uv 官方文档。