# 学习助手 (LearningAssistant)

AI 驱动的编程学习辅助工具，通过浏览器扩展与桌面端协同工作，实现自动题目获取、AI 代码生成、智能纠错和自动代码输入，**无视头歌等平台的禁止粘贴限制**。

## 背景

在线编程学习平台（如头歌 Educoder）通常禁止粘贴代码，且题目描述复杂时手动编写效率低。本工具通过浏览器扩展自动提取题目，调用 AI 生成代码，再自动写入编辑器，实现一键答题全流程自动化。

## 功能特性

- **无视禁止粘贴**：通过编辑器 API 直接写入代码，绕过粘贴限制
- **AI 代码生成**：基于题目描述自动生成代码，支持 Python、Java、C++、JavaScript 等多种语言
- **智能纠错**：自动检测测试失败结果，调用 AI 生成修复代码
- **浏览器扩展**：浮动面板支持拖拽，自动提取页面题目与代码
- **多编辑器适配**：支持 Monaco、CodeMirror、Ace、textarea、contentEditable 等主流在线编辑器
- **跨 iframe 支持**：自动追踪 iframe 内编辑器焦点，跨 frame 写入代码
- **模拟键盘输入**：桌面端可模拟键盘逐行输入代码（适用于严格限制粘贴的场景）
- **代码双向同步**：扩展端与桌面端实时同步代码和题目内容
- **配置同步**：扩展端与桌面端双向同步输入参数（间隔、特殊字符等）
- **OCR 截图识别**：支持对题目截图进行 OCR 文字识别
- **系统托盘**：最小化到托盘继续运行
- **跨平台支持**：Windows / macOS / Linux

## 系统架构

```
┌─────────────────┐         WebSocket         ┌─────────────────┐
│   浏览器扩展      │◄──────────────────────►│    桌面端         │
│  (Content Script) │        ws://host:port    │  (Python GUI)    │
│                   │                          │                  │
│  - 提取题目       │     题目/代码/测试结果     │  - AI 代码生成    │
│  - 写入编辑器     │◄──────────────────────►│  - 智能纠错       │
│  - 浮动面板       │     生成代码/纠错代码     │  - 模拟键盘输入   │
│  - OCR 识别       │                          │  - 系统托盘       │
└─────────────────┘                          └─────────────────┘
                      │
                      │ MAIN 世界注入
                      ▼
              ┌─────────────────┐
              │   页面编辑器      │
              │  Monaco/CM/Ace  │
              └─────────────────┘
```

**通信流程**：
1. 浏览器扩展通过 Content Script 提取题目，通过 WebSocket 发送给桌面端
2. 桌面端调用 AI API 生成代码，通过 WebSocket 返回给扩展
3. 扩展通过 Background Service Worker 在 MAIN 世界注入 `insertIntoPageEditor` 函数，直接调用编辑器 API 写入代码
4. 扩展读取测试结果，失败时自动请求桌面端纠错

## 技术栈

**桌面端**

| 技术 | 用途 |
|---|---|
| Python 3.13+ | 主语言 |
| customtkinter | GUI 界面（现代化主题） |
| AsyncOpenAI | AI SDK（兼容 OpenAI 协议） |
| websockets | WebSocket 服务器 |
| pyautogui / keyboard | 模拟键盘输入 |
| pyperclip | 剪贴板操作 |
| pystray | 系统托盘 |
| python-dotenv | 环境变量管理 |
| selenium | Chrome for Testing 自动启动 |
| uv | 包管理 |

**浏览器扩展**

| 技术 | 用途 |
|---|---|
| Manifest V3 | 扩展规范 |
| Service Worker | Background 脚本 |
| Content Script | 页面交互与浮动面板 |
| Shadow DOM | 面板样式隔离 |
| MAIN 世界注入 | 直接调用页面编辑器 API |

## 安装

### 环境要求

- Python >= 3.13
- Chrome 或 Edge 浏览器
- 有效的 AI API Key（兼容 OpenAI 协议，如阿里通义、DeepSeek、OpenAI 等）

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/hnlinyh/LearningAssistant.git
cd LearningAssistant

# 安装依赖（推荐使用 uv）
uv sync

# 或使用 pip
pip install -e .
```

### 安装浏览器扩展

**自动安装**（推荐）：

1. 启动桌面端后，在「扩展管理」Tab 点击「启动 Chrome for Testing」或「启动 Edge」
2. 桌面端自动启动浏览器并加载扩展

**手动安装**：

1. 打开 Chrome/Edge，访问 `chrome://extensions/`（或 `edge://extensions/`）
2. 开启「开发者模式」
3. 点击「加载已解压的扩展程序」，选择项目中的 `chrome/chrome` 文件夹

## 运行

```bash
python main.py
```

或使用入口命令：

```bash
learning-assistant
```

## 配置

### 环境变量

首次运行自动创建 `.env` 文件：

```env
# AI 模型配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen3-coder-plus

# 服务器配置
WS_HOST=localhost
WS_PORT=8000
```

### AI 模型配置

支持所有兼容 OpenAI 协议的 API 服务：

| 服务商 | Base URL | 推荐模型 |
|---|---|---|
| 阿里通义 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3-coder-plus` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-coder` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| 自部署 | 你的服务地址 | 任意兼容模型 |

在桌面端「AI 模型」Tab 中输入 API Key 和 Base URL，点击「获取模型」拉取可用模型列表，选择目标模型即可。

### 配置文件

| 文件 | 说明 |
|---|---|
| `.env` | API 配置和服务器端口 |
| `~/.learning_assistant/config.ini` | 自定义语言列表、机器码 |
| `chrome/chrome/server-config.json` | 扩展端 WebSocket 地址（启动服务器时自动写入） |

## 使用方法

### 快速开始

1. **启动桌面端**：运行 `python main.py`
2. **配置 AI 模型**：在「AI 模型」Tab 配置 API Key 和 Base URL，获取并选择模型
3. **启动服务器**：在「服务器」Tab 点击「启动服务器」，WebSocket 服务器开始运行
4. **启动浏览器**：在「扩展管理」Tab 启动浏览器（Chrome for Testing 或 Edge）
5. **使用扩展**：浏览器打开编程学习平台，浮动面板自动连接到桌面端

### 自动答题流程

```
1. 浏览器扩展自动提取页面题目
       ↓
2. 通过 WebSocket 发送题目到桌面端
       ↓
3. 桌面端调用 AI 生成代码
       ↓
4. 生成代码通过 WebSocket 返回给扩展
       ↓
5. 扩展将代码写入编辑器（直接调用编辑器 API / 模拟键盘输入）
       ↓
6. 可选：扩展读取测试结果，失败时自动纠错
```

### 智能纠错流程

当测试失败时，扩展自动将测试失败信息发送给桌面端，桌面端调用 AI 生成修复代码并返回，扩展自动替换编辑器中的代码。

### 模拟键盘输入

对于严格禁止粘贴的平台，桌面端提供模拟键盘输入功能：

- **逐行输入**：逐行模拟键盘打字，可配置输入间隔
- **粘贴模式**：通过剪贴板粘贴（Ctrl+V）
- **ESC 取消**：输入过程中按 ESC 可随时中断
- **倒计时**：输入前 3 秒倒计时，方便切换到目标窗口

### 桌面端 Tab 说明

| Tab | 功能 |
|---|---|
| **AI 模型** | 配置 API Key / Base URL，获取模型列表，选择和测试模型 |
| **桌面输入** | 手动输入代码，模拟键盘输入，粘贴代码 |
| **扩展管理** | 自动/手动安装浏览器扩展，启动 Chrome for Testing 或 Edge |
| **服务器** | 配置端口，启动/停止 WebSocket 服务器，查看运行状态 |

## 项目结构

```
LearningAssistant/
├── main.py                    # 应用入口
├── path_config.py             # 全局路径常量
├── pyproject.toml             # 项目配置与依赖
├── .env                       # 环境变量（自动创建）
├── core/
│   ├── server.py              # WebSocket 服务器管理
│   └── assistant.py           # AI 对话、代码生成、智能纠错
├── gui/
│   ├── main_window.py         # 主窗口（customtkinter）
│   ├── model_manager.py       # 模型获取与测试
│   ├── themes.py              # 主题配色常量
│   ├── widgets/
│   │   └── log_panel.py       # 日志面板组件
│   └── tabs/
│       └── input_tab.py       # 桌面输入 Tab 组件
├── utils/
│   ├── config.py              # 配置读写（.env + config.ini）
│   ├── input_simulator.py     # 键盘模拟输入（跨平台）
│   └── extension_setup.py     # 浏览器扩展安装与启动
└── chrome/chrome/              # 浏览器扩展
    ├── manifest.json          # 扩展配置（Manifest V3）
    ├── background.js          # Service Worker
    ├── content.js             # Content Script（浮动面板 + 题目提取）
    ├── content.css            # 扩展样式
    └── server-config.json     # 服务器地址配置（自动写入）
```

## 浏览器扩展详解

### Content Script 功能

- **浮动面板**：在页面右下角显示可拖拽的操作面板
- **题目提取**：自动识别并提取页面中的题目描述
- **代码读取**：从编辑器中读取当前已有代码
- **代码写入**：将 AI 生成的代码写入目标编辑器
- **测试结果读取**：读取评测结果，检测是否有失败的测试
- **OCR 识别**：对题目截图调用 OCR API 进行文字识别

### Background Service Worker 功能

- **编辑器注入**：在 MAIN 世界执行 `insertIntoPageEditor`，直接调用编辑器原生 API
- **跨 iframe 路由**：追踪 iframe 内的编辑器焦点，精准定位写入目标
- **配置同步**：读取 `server-config.json` 并定期刷新，同步 WebSocket 地址
- **编辑器检测**：评分算法自动选择最佳目标编辑器

### 支持的编辑器

| 编辑器 | 插入方式 | 常见平台 |
|---|---|---|
| Monaco Editor | `executeEdits` API | 头歌、力扣 |
| CodeMirror | `replaceSelection` API | 牛客、部分 OJ |
| Ace Editor | `session.replace` API | 旧版在线编辑器 |
| textarea | `setRangeText` | 普通 HTML 文本框 |
| contentEditable | `execCommand` / Range API | 富文本编辑区域 |

## 支持的平台

| 平台 | URL 模式 | 说明 |
|---|---|---|
| 头歌 Educoder | `educoder.net/tasks/*` `shixuns/*` `classrooms/*` | 主要支持，自动提取题目 |
| 力扣 LeetCode | `leetcode.cn/problems/*` | Monaco 编辑器 |
| 牛客网 | `nowcoder.com/practice/*` | CodeMirror 编辑器 |
| yhsun.cn OJ | `yhsun.cn/oj/*` | 自建 OJ 平台 |

## 开发指南

### 添加新语言

在 `gui/language_manager.py` 的默认语言列表中添加语言名称。

### 自定义 AI 提示词

编辑 `core/assistant.py` 中的 `_get_system_prompt` 方法，修改 `GENERATION_RULES` 和 `REVISION_RULES`。

### 扩展支持的编辑器

在 `chrome/chrome/background.js` 的 `insertIntoPageEditor` 函数中添加新的编辑器适配逻辑。

### 添加新平台支持

在 `chrome/chrome/manifest.json` 的 `content_scripts.matches` 和 `host_permissions` 中添加新的 URL 模式，并在 `content.js` 中添加对应的题目提取逻辑。

## 键盘模拟输入细节

`InputSimulator` 类根据操作系统自动选择输入方式：

| 平台 | 优先方式 | 备选方式 |
|---|---|---|
| Windows | `keyboard.write()` | `pyperclip` + Ctrl+V |
| macOS | `keyboard.write()` | `pyperclip` + Cmd+V |
| Linux (xdotool) | `xdotool type` | `pyperclip` + Ctrl+V |
| Linux (无 xdotool) | `keyboard.write()` | `pyperclip` + Ctrl+V |

## WebSocket 通信协议

扩展与桌面端通过 WebSocket 通信，主要消息类型：

| 方向 | 类型 | 说明 |
|---|---|---|
| 扩展 → 桌面 | `content_auto_input` | 自动提取的题目 + 当前代码 |
| 扩展 → 桌面 | `test_results` | 测试失败结果 |
| 扩展 → 桌面 | `simulate_input` | 请求模拟键盘输入 |
| 扩展 → 桌面 | `sync_code` | 同步编辑器中的代码到桌面端 |
| 扩展 → 桌面 | `sync_input_config` | 同步输入配置参数 |
| 桌面 → 扩展 | `code_solution` | AI 生成的代码 |
| 桌面 → 扩展 | `code_revision` | AI 纠错后的代码 |
| 桌面 → 扩展 | `input_complete` | 模拟输入完成 |
| 桌面 → 扩展 | `progress_update` | 输入进度 |
| 双向 | `config_info` | 模型配置信息 |

## 许可证

MIT License
