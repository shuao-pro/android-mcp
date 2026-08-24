# Android MCP Server

**基于 MCP 协议的 AI 驱动 Android 设备自动化控制。**

通过 Claude Desktop、Cherry Studio、Kai 9000、或内置的 AI 对话 Web 界面，用自然语言操控你的 Android 手机。

<p align="center">
  <a href="./README.md">🇺🇸 English</a> &nbsp;|&nbsp; <b>🇨🇳 中文</b>
</p>

<p align="center">
  <a href="https://github.com/shuao-pro/android-mcp"><img src="https://img.shields.io/badge/GitHub-shuao--pro%2Fandroid--mcp-181717?logo=github" alt="GitHub"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/MCP-1.8+-purple" alt="MCP">
  <img src="https://img.shields.io/badge/version-2.1.0-orange" alt="v2.1.0">
</p>

---

## 🏗️ 架构

三个层级协同工作，把自然语言请求转化为设备上的系统级操作：

```mermaid
flowchart LR
    subgraph CLIENTS["🤖 MCP 客户端"]
        direction TB
        C1["Claude Desktop<br/>stdio / SSE"]
        C2["Kai 9000<br/>Streamable HTTP"]
        C3["Cherry Studio<br/>Streamable HTTP"]
        C4["Web 控制台<br/>浏览器 · :8080"]
    end

    subgraph SERVER["🐍 Python 服务器 · android_mcp/"]
        direction TB
        S1["FastMCP<br/>37 个工具 · :9000<br/>/sse + /mcp"]
        S2["Web GUI · FastAPI<br/>:8080 · WebSocket"]
        S3["tools/<br/>薄封装层"]
        S4["bridge/<br/>JSON-RPC 传输层"]
        S5["vision/<br/>AI 元素定位"]
        S6["safety/<br/>风险分级 · 用户确认"]
        S7["tasks/<br/>提交 · 轮询 · 取结果"]
        S1 --- S3
        S3 --- S4
        S3 --- S6
        S3 --- S7
        S7 --- S4
        S2 --- S4
        S2 --- S5
    end

    subgraph PHONE["📱 Android 应用 · Kotlin · Root / Shizuku"]
        direction TB
        P1["HttpServer<br/>:18080"]
        P2["Router<br/>JSON-RPC 分发"]
        P3["api/<br/>shell · input · file · system"]
        P4["PrivilegeExecutor<br/>AUTO / ROOT / SHIZUKU"]
        P5["Root (su)<br/>UID 0"]
        P6["Shizuku<br/>UID 2000"]
        P7["TaskApi + TaskManager<br/>异步任务队列"]
        P1 --- P2
        P2 --- P3
        P2 --- P7
        P3 --- P4
        P7 --- P4
        P4 --- P5
        P4 --- P6
    end

    C1 --> S1
    C2 --> S1
    C3 --> S1
    C4 --> S2
    S4 -->|"HTTP JSON-RPC · X-MCP-Token<br/>ADB 转发 tcp:18080"| P1
    S5 -.->|"Claude Vision / GPT-4o"| V["🧠 视觉 API"]
```

### 组件说明

| 层级 | 组件 | 职责 | 关键技术 |
|------|------|------|----------|
| **客户端** | Claude Desktop / Kai 9000 / Cherry Studio | 通过 MCP 发送工具调用 | stdio、SSE、Streamable HTTP |
| | Web 控制台 | 浏览器面板、实时画面、AI 对话 | FastAPI + WebSocket |
| **Python 服务器** | `server.py`（FastMCP） | 注册 37 个工具，处理 MCP 协议 | FastMCP |
| | `bridge/` | 发送 JSON-RPC 到设备，自动 ADB 转发 | httpx、JSON-RPC 2.0 |
| | `tools/` | 对 `bridge/` 的 `@bridge_call` 薄封装 | 装饰器 |
| | `safety/` | 风险分级 + 用户确认门控 | MCP elicitation、SAFETY_MODE |
| | `web/` | 控制台 API、聊天、scrcpy 推流 | FastAPI、uvicorn |
| | `vision/` | AI 屏幕元素识别 | Claude Vision / GPT-4o |
| | `tasks/` | 长任务提交 / 轮询 / 取结果 | task.submit/status/result RPC |
| **Android 应用** | `HttpServer` | 内嵌 HTTP 服务器 :18080，token 鉴权 | Java `ServerSocket` |
| | `Router` | JSON-RPC 方法分发 | JSON-RPC 2.0 |
| | `api/*` | Shell、触控、应用、文件、系统、任务操作 | PrivilegeExecutor（Root / Shizuku） |
| | `TaskManager` / `TaskApi` | 后台任务队列 + JSON-RPC API | 线程池、任务状态机 |
| | `util/` | 特权执行器 + token 存储 | `PrivilegeExecutor`、`RootHelper`、`ShizukuHelper`、`TokenStore` |

### 请求生命周期

每个工具调用都走同一条链路 —— 以 `click(x, y)` 为例：

1. **客户端** 通过 MCP（`:9000`）或 Web 控制台（`:8080`）发送 `click(x, y)`。
2. **FastMCP / FastAPI** 将其路由到 `tools/` 中对应的封装函数。
3. **`safety/`** 对操作进行风险分级；高危命令（破坏性 shell、写入受保护路径、卸载/清除应用等）会通过 MCP elicitation 触发用户交互式确认，同意后才继续。
4. **`bridge/_core.py`** 序列化为 JSON-RPC 2.0 请求，附带 `X-MCP-Token` 头，POST 到 `http://127.0.0.1:18080/mcp`（必要时自动重建 ADB 转发）。
5. **`HttpServer`** 校验 token 后，交给 `Router`。
6. **`Router`** 分发到对应的 `api/*` 模块（如 `InputApi.tap`），通过 **Shizuku**（UID 2000）或 **Root**（su，UID 0）执行 —— 无需 root 即可使用，root 设备可获得完整 root 权限。
7. JSON-RPC 结果沿原链路返回给调用方。

### 端口与传输

| 端口 | 服务 | 传输方式 | 使用者 |
|------|------|----------|--------|
| `:9000/sse` | MCP（SSE） | HTTP SSE | Claude Desktop（远程）、Web 前端 |
| `:9000/mcp` | MCP（Streamable HTTP） | HTTP POST/GET | Kai 9000、Cherry Studio |
| `:8080` | Web 控制台 | HTTP + WebSocket | 浏览器 |
| `:18080` | Android 桥接 | HTTP JSON-RPC（ADB 转发） | Python `bridge/` |
| *(stdio)* | MCP（stdio） | 本地管道 | Claude Desktop（本地） |

> 🔒 **通信鉴权**：Python 网关 ↔ Android 应用通过共享 `X-MCP-Token` 统一鉴权。App 随机生成 token 并显示在界面，复制到 `.env` 的 `ANDROID_TOKEN=` 即可。默认 `MCP_HOST=127.0.0.1`（仅本机访问）。

> 💡 服务器可直接在手机上运行（Termux / Kai 9000）。设置 `ANDROID_HOST=127.0.0.1` — 无需 ADB。
## 功能特性

### 设备控制（37 个 MCP 工具）

| 分类 | 工具 |
|------|------|
| **设备状态** | `health_check`、`get_device_info`、`get_battery_info` |
| **Shell** | `shell` — 执行任意 ADB 级命令 |
| **触控** | `click`、`long_click`、`swipe`、`drag`、`type_text`、`press_key` |
| **应用管理** | `open_app`、`close_app`、`clear_app_data`、`install_app`、`uninstall_app`、`get_current_app`、`list_installed_apps` |
| **屏幕** | `take_screenshot`、`get_ui_hierarchy` |
| **文件** | `read_file`、`write_file`（支持 `/data/data` 受限目录） |
| **系统** | `get_system_setting`、`put_system_setting`、`set_clipboard`、`get_clipboard`、`get_notifications`、`start_activity` |
| **特权模式** | `get_privilege_mode`、`set_privilege_mode` — 切换设备执行后端（auto / shizuku / root） |
| **长任务** | `submit_task`、`get_task_status`、`get_task_result`、`cancel_task`、`list_tasks`、`run_task_and_wait` — 把长命令跑成后台任务 |
| **AI 视觉** | `find_element` — AI 定位屏幕元素，`click_element` — 识别+点击一步完成 |

### 🛡️ 权限审查（安全防护）

高危设备操作会被门控，需用户确认后才执行：

- 破坏性 shell 命令（`rm -rf`、`dd`、`mkfs`、`mount`、`reboot`、`su`、`pm uninstall/clear` …）
- 写入受保护路径（`/system`、`/data`、`/vendor` …）
- 应用安装 / 卸载 / 清除数据、系统设置修改

`SAFETY_MODE` 控制策略：`confirm`（默认）通过 MCP elicitation 向用户弹窗确认；`permissive` 全部放行；`strict` 直接拦截高/中危操作。

### 🔓 特权模式（Root / Shizuku）

Android 应用通过统一的 **PrivilegeExecutor** 执行命令，支持三种模式：

| 模式 | 后端 | 适用 |
|------|------|------|
| `root` | `su`（uid 0） | 已 root 设备（Magisk / KernelSU / APatch / SuperSU） |
| `shizuku` | Shizuku binder（uid 2000） | 未 root 但已安装 Shizuku 的设备 |
| `auto`（默认） | root → shizuku 回退 | 有 root 用 root，否则用 Shizuku |

可在 Android App 界面、Web 控制台，或通过 `set_privilege_mode` MCP 工具切换。

### ⏳ 长任务异步执行

可能超过 30 秒 HTTP 超时的命令，会作为后台异步任务在设备上运行：

- `submit_task` / `run_task_and_wait` — 后台运行命令并轮询直到结束
- `get_task_status` / `get_task_result` / `cancel_task` / `list_tasks` — 监控与取消任务
- 设备端 `TaskManager` 用独立线程池（10 并发）运行命令，输出截断 + 自动清理

### 🤖 多步智能体

Web 控制台的 AI 对话采用闭环智能体：串联多个工具调用（截图 + 视觉校验、长任务、失败重试）直到目标完成 —— 最多 10 步。

### AI 视觉

- 接入 Claude Vision / GPT-4o / 自定义 API 进行屏幕元素识别
- 自然语言描述 → 像素坐标 → 自动点击
- 示例：`find_element("登录按钮")` → `{center_x: 540, center_y: 960, confidence: 0.95}`

### Web 控制台

- **AI 对话** — 多步智能体：描述目标，自动串联工具调用（截图+视觉校验、长任务、失败重试）直到完成
- **实时画面** — 10fps WebSocket 推流，点击画面直接触控
- **scrcpy 投屏** — 一键启动原生低延迟投屏窗口
- **连接向导** — 5 步引导式配置，自动检测前置条件 + 显示 MCP SSE 地址
- **设置面板** — 可视化配置 API 供应商 + ADB 设备管理，自动同步 .env
- **特权模式** — 在侧边栏切换 自动 / Shizuku / Root
- **中/English** — 完整国际化支持
- **Shell 终端** — 浏览器内实时 ADB Shell

### MCP 客户端

将任意 MCP 兼容客户端连接到服务器：

| 客户端 | 传输方式 | 端点 | 平台 |
|--------|----------|------|------|
| **Kai 9000** | Streamable HTTP | `:9000/mcp` | Android (F-Droid) |
| **Cherry Studio** | Streamable HTTP | `:9000/mcp` | Windows / macOS / Linux |
| **Claude Desktop** | SSE / stdio | `:9000/sse` 或 `stdio` | Windows / macOS / Linux |
| **Termux + curl** | SSE | `:9000/sse` | Android (Termux) |

> **Cherry Studio 配置:** MCP 类型选 `streamableHttp`，URL 填 `http://<局域网IP>:9000/mcp`。
> 或直接导入项目根目录的 `cherry-studio-mcp.json`。

### MCP 传输模式

| 模式 | 端点 | 适用场景 |
|------|------|----------|
| `stdio` | (本地管道) | Claude Desktop 本地集成 |
| SSE | `:9000/sse` | Claude Desktop 远程、Web 前端 |
| Streamable HTTP | `:9000/mcp` | Kai 9000、现代 MCP 客户端 |
| **Combined**（默认） | **两者同端口 `:9000`** | **SSE + Streamable HTTP 同时运行** |

---


---

## 🔗 链接

| 资源 | URL |
|------|-----|
| **GitHub** | [github.com/shuao-pro/android-mcp](https://github.com/shuao-pro/android-mcp) |
| **Issues** | [报告问题 / 请求功能](https://github.com/shuao-pro/android-mcp/issues) |
| **README English** | [README.md](./README.md) |

## 快速开始

### 前置条件

- Python 3.10+
- Android 设备已安装 **Shizuku**（或已 root 的设备，二选一）
- ADB（Android SDK Platform Tools）
- scrcpy（可选，用于原生投屏）

### 1. 安装

```bash
git clone https://github.com/shuao-pro/android-mcp.git
cd android-mcp
pip install -e .
```

### 2. 环境配置

```bash
# 首次配置（创建 .env）
bash scripts/setup.sh
```

或手动：
```bash
cp .env.example .env
```

安装 Android APK 到手机：
```bash
# 使用预编译 APK（推荐）
adb install android/app/build/outputs/apk/debug/app-debug.apk

# 或从源码编译
cd .. && cd "android-mcp apk" && .\gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

### 3. 手机端操作

1. 启动 **Shizuku**（授予 root 或无线调试权限）；或使用已 root 的设备
2. 打开 **Android MCP** 应用 → 选择模式（自动 / Shizuku / Root）→ 授予权限 → 点击 **启动**
3. 通知栏显示"MCP 服务运行中"（端口 18080）
4. 复制界面显示的 **鉴权 Token**，填入 `.env` 的 `ANDROID_TOKEN=`

### 4. 启动服务

```bash
# 一键启动（SSE + Web GUI + ADB 转发）
./start.sh

# Windows 系统
start.bat
```

浏览器自动打开 `http://127.0.0.1:8080`。

### 5. 连接 MCP 客户端

在 Web 控制台中打开 **菜单 → 配置向导** 查看 MCP 地址：

| 客户端 | 端点 |
|--------|------|
| **Kai 9000**（手机） | `http://192.168.x.x:9000/mcp` |
| **Claude Desktop**（远程） | `http://192.168.x.x:9000/sse` |
| **同设备**（Termux） | `http://127.0.0.1:9000/sse` 或 `/mcp` |

将地址添加到 Kai 9000（设置 → MCP 服务器 → 添加）或 Claude Desktop：

```json
{
  "mcpServers": {
    "android": {
      "command": "python",
      "args": ["-m", "android_mcp.main", "--mode", "mcp"]
    }
  }
}
```

现在即可通过对话操控手机 — "打开设置"、"截屏"、"点击搜索按钮"。

---

## 配置说明

编辑 `.env` 文件：

```env
# 设备连接
ANDROID_HOST=127.0.0.1
ANDROID_PORT=18080

# Android 桥接鉴权 Token（App 界面显示，复制到这里）
ANDROID_TOKEN=

# Web 控制台
WEB_HOST=127.0.0.1
WEB_PORT=8080

# MCP 服务（SSE + Streamable HTTP）— 供 Kai 9000 等客户端接入
# 默认 127.0.0.1（仅本机，安全）；如需手机/WiFi 客户端连接改为 0.0.0.0
MCP_HOST=127.0.0.1
MCP_PORT=9000

# AI 视觉（可选 — 启用 AI 对话和元素识别）
VISION_PROVIDER=anthropic       # anthropic | openai | custom
VISION_API_KEY=sk-ant-api03-xxxxx
VISION_MODEL=                   # 留空使用默认模型
VISION_API_BASE=                # 仅 custom 供应商需要
```

---

## CLI 命令

```bash
# 启动模式
python -m android_mcp.main --mode all-sse   # SSE + Streamable HTTP + Web GUI（默认）
python -m android_mcp.main --mode mcp       # stdio 模式（Claude Desktop）
python -m android_mcp.main --mode mcp-sse   # SSE + Streamable HTTP（无头）
python -m android_mcp.main --mode mcp-http  # Streamable HTTP 模式
python -m android_mcp.main --mode web       # 仅 Web GUI

# 进程管理
python -m android_mcp.gateway start         # 后台启动
python -m android_mcp.gateway status        # 查看状态
python -m android_mcp.gateway stop          # 停止服务
python -m android_mcp.gateway forward       # ADB 端口转发
```

## 项目结构

```
android-mcp/
├── android_mcp/
│   ├── server.py          # FastMCP 服务定义（工具注册）
│   ├── main.py            # 入口（模式分发）
│   ├── config.py          # 环境配置（.env 加载）
│   ├── safety.py          # 风险分级 + 用户确认门控
│   ├── console.py         # 彩色控制台输出
│   ├── utils.py           # 局域网 IP + 版本工具
│   ├── gateway.py         # CLI 进程管理
│   ├── bridge/            # 底层 Android HTTP 桥接
│   │   ├── __init__.py    # 重新导出所有桥接函数
│   │   ├── _core.py       # JSON-RPC 传输 + ADB 转发
│   │   ├── device.py      # 健康、信息、截图、Shell、重启
│   │   ├── input.py       # 点击、滑动、拖拽、按键、输入
│   │   ├── apps.py        # 应用管理
│   │   ├── system.py      # 电池、剪贴板、通知、系统设置、模式
│   │   ├── files.py       # 文件读写/列表/删除
│   │   └── tasks.py       # 长任务提交/状态/结果/取消/列表
│   ├── tools/             # MCP 工具层（对 bridge 的薄封装）
│   │   ├── __init__.py    # register_all_tools()
│   │   ├── decorators.py  # @bridge_call 错误处理装饰器
│   │   ├── device.py      # 健康、信息、电池、截图、UI 层级
│   │   ├── input.py       # 触控、滑动、按键
│   │   ├── apps.py        # 应用管理
│   │   ├── system.py      # Shell、设置、剪贴板、特权模式
│   │   ├── files.py       # 文件读写
│   │   ├── tasks.py       # 任务工具（提交/轮询/run_task_and_wait）
│   │   └── vision.py      # AI 元素识别
│   ├── vision/            # 视觉模型客户端
│   │   ├── models.py      # 数据结构 + Protocol
│   │   ├── clients.py     # Anthropic + OpenAI 客户端（+ 屏幕描述）
│   │   └── prompts.py     # 提示词 + 解析器
│   └── web/               # Web 控制台
│       ├── server.py      # FastAPI + WebSocket
│       ├── chat_agent.py  # 多步智能体循环（工具串联 + 视觉校验）
│       ├── scrcpy_bridge.py # scrcpy + 画面推流
│       └── static/        # HTML/CSS/JS 前端
├── android/               # Android APK 项目
│   ├── app/src/main/
│   │   ├── java/com/example/androidmcp/
│   │   │   ├── App.kt             # Application 入口
│   │   │   ├── MainActivity.kt    # 主界面 + 特权模式 + 授权
│   │   │   ├── McpService.kt      # 前台服务
│   │   │   ├── api/
│   │   │   │   ├── FileApi.kt     # 文件读写/删除
│   │   │   │   ├── InputApi.kt    # 触控、滑动、按键
│   │   │   │   ├── PackageApi.kt  # 应用安装/卸载
│   │   │   │   ├── ShellApi.kt    # Shell 命令执行
│   │   │   │   ├── SystemApi.kt   # 截图、剪贴板、系统设置、模式
│   │   │   │   └── TaskApi.kt     # 任务提交/状态/结果/取消/列表
│   │   │   ├── server/
│   │   │   │   ├── HttpServer.kt  # 内嵌 HTTP 服务器 (:18080)
│   │   │   │   └── Router.kt      # JSON-RPC 方法路由
│   │   │   └── util/
│   │   │       ├── PrivilegeExecutor.kt # 模式路由（AUTO/ROOT/SHIZUKU）
│   │   │       ├── RootHelper.kt        # su 后端（uid 0）
│   │   │       ├── ShizukuHelper.kt     # Shizuku binder 后端
│   │   │       ├── TaskManager.kt       # 后台任务队列 + 状态机
│   │   │       ├── ExecResult.kt        # 命令结果 + 进程句柄
│   │   │       └── TokenStore.kt        # 桥接鉴权 Token（生成 + 持久化）
│   │   └── res/                   # 布局、图标、字符串资源
│   ├── gradle/                    # Gradle 构建系统
│   ├── build.gradle.kts
│   └── settings.gradle.kts
├── scripts/setup.sh       # 首次配置脚本
├── tests/                 # 测试脚本
│   ├── test_adb.py        # ADB 桥接测试
│   └── test_all.py        # 端到端测试
├── start.sh               # 一键启动脚本
├── start.bat              # Windows 启动脚本
├── pyproject.toml
└── .env.example
```

---

## 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| Android | 11+ (API 30+) |
| 手机端 | Shizuku 已安装并运行 |
| ADB | Platform Tools（用于端口转发） |
| scrcpy | 可选（原生投屏） |
| AI 视觉 | Anthropic/OpenAI API Key（可选） |
| MCP 客户端 | Kai 9000（F-Droid）、Claude Desktop、或任意 SSE/stdio MCP 客户端 |

---

## 许可证

MIT
