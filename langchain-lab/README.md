# langchain-lab

面向 LangChain / LangGraph 学习的 Docker 开发环境（**Python 3.11**，单镜像），用于在**多台电脑间保持环境一致**。

> 本仓库的项目级管理规则见 [RULES.md](RULES.md)，开发本仓库前请先阅读。

## 目录结构

```
langchain-lab/
├── Dockerfile          # 镜像定义（uv + python3.11-slim）
├── RULES.md            # 项目级管理规则（开发前必读）
├── pyproject.toml      # 依赖声明（版本区间）
├── uv.lock             # 锁定精确版本（跨机一致性关键）
├── .env.example        # 环境变量模板（复制为 .env 使用）
├── .env                # 你的密钥（不入库，含 Git 忽略的敏感信息）
├── .gitignore
├── .dockerignore
├── dev.ps1             # 快捷进入常驻容器（不存在则自动创建）
├── rebuild.ps1         # 重建镜像
└── examples/
    ├── test_01/        # 第 1 章：打造你的第一个 Agent
    ├── test_02/        # 第 2 章：Chat Model 常规/高级用法（bind_tools/结构化输出）
    ├── test_03/        # 第 3 章：工具高级特性（args_schema/异常处理/return_direct）
    ├── test_4/         # 第 4 章：工具访问（InjectedState/InjectedStore/SQLite持久化）
    └── 学习日志.md      # 各章节学习的沉淀记录
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

编辑 `.env`，填入服务商信息：
- `DEEPSEEK_API_KEY`：本项目模型固定为 `deepseek-v4-flash`，填入对应的 DeepSeek 密钥。
- `QWEATHER_API_HOST` / `QWEATHER_API_KEY`：和风天气账号专属 Host（控制台-设置查看）与 Key。

> 和风天气 2026 年起强制使用账号专属 API Host，Host 与 Key 均属敏感认证信息，只写进 `.env`，切勿提交。

### 3. 运行（常驻容器）

一条命令进入常驻容器 shell（容器 `langlab` 不存在会自动创建，并挂载当前目录为 `/workspace`）：

```powershell
.\dev.ps1
```

进入容器后即为常规终端，直接使用 `python` 运行脚本：

```bash
python examples/test_01/agent.py
```

不想进 shell、只想快速跑一次脚本：

```powershell
.\dev.ps1 examples/test_01/agent.py
```

常驻容器用完后可手动停止 / 删除（下次 `.\dev.ps1` 会自动重建）：

```powershell
docker stop langlab
docker rm langlab
```

## 两台电脑的一致性保证

1. 本项目（含 `uv.lock`、`Dockerfile`、`examples/`）纳入 Git 仓库。
2. 换机器时 `git clone` 到同样的路径，执行 `.\rebuild.ps1` 生成**完全一致**的镜像与依赖版本。
3. `.env` 不入库，各自机器维护自己的 Key；代码与依赖保持一致。

## 依赖清单

由 `uv.lock` 锁定（首次生成时的主要版本）：

- langchain / langchain-core / langchain-openai / langchain-deepseek
- langgraph / langgraph-checkpoint-sqlite / langgraph-cli / langgraph-prebuilt / langgraph-sdk
- langsmith（可观测性）、python-dotenv

## 添加 / 升级依赖

编辑 `pyproject.toml` 中的 `dependencies`，然后重新生成锁文件（在容器内执行，保证针对 Python 3.11）：

```powershell
docker run --rm -v "${PWD}:/work" -w /work ghcr.io/astral-sh/uv:python3.11-bookworm-slim uv lock
.\rebuild.ps1
```

> 提示：国内网络下可通过设置 `UV_DEFAULT_INDEX` 指向镜像源加速，具体见 uv 官方文档。