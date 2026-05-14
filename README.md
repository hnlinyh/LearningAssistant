# 学习助手 (LearningAssistant)

> AI 驱动的编程学习辅助工具，通过浏览器扩展与桌面端协同工作，实现自动题目获取、AI 代码生成、智能纠错和自动代码输入。

## 功能特性

- **AI 代码生成**：基于题目描述自动生成代码，支持多种编程语言
- **智能纠错**：自动检测测试失败结果，生成修复代码
- **浏览器扩展**：浮动面板支持拖拽、调整大小，自动提取页面题目
- **多编辑器适配**：支持 Monaco、CodeMirror、Ace 等主流在线编辑器
- **模拟键盘输入**：桌面端可模拟键盘逐行输入代码
- **配置同步**：扩展端与桌面端双向同步输入参数
- **系统托盘**：最小化到托盘继续运行
- **跨平台支持**：Windows / macOS / Linux

## 技术栈

**桌面端**
- Python 3.13+
- GUI：customtkinter
- AI SDK：openai（兼容 OpenAI 协议）
- WebSocket：websockets
- 包管理：uv

**浏览器扩展**
- Manifest V3
- 纯 JavaScript

## 安装

### 环境要求

- Python >= 3.13
- Chrome 或 Edge 浏览器
- 有效的 AI API Key（兼容 OpenAI 协议）

### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd LearningAssistant

# 安装依赖（使用 uv）
uv sync

# 或使用 pip
pip install -e .
```

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
OPENAI_API_KEY=<your-api-key>
OPENAI_BASE_URL=<api-base-url>
OPENAI_MODEL=<model-name>
WS_HOST=localhost
WS_PORT=8001
```

### 配置文件

- `.env`：API 配置和服务器端口
- `~/.learning_assistant/config.ini`：自定义语言列表、机器码

## 使用方法

1. **启动桌面端**：运行 `python main.py`
2. **配置 AI 模型**：在"AI 模型"Tab 配置 API Key 和 Base URL，获取并选择模型
3. **启动服务器**：在"服务器"Tab 启动 WebSocket 服务器
4. **启动浏览器**：在"扩展管理"Tab 启动浏览器（Chrome for Testing 或 Edge）
5. **使用扩展**：浏览器打开编程学习平台，浮动面板自动连接到桌面端

### 自动答题流程

1. 浏览器扩展自动提取页面题目
2. 桌面端调用 AI 生成代码
3. 扩展将代码写入编辑器
4. 可选：模拟键盘输入或直接粘贴

## 项目结构

```
LearningAssistant/
├── main.py                    # 应用入口
├── path_config.py             # 全局路径常量
├── pyproject.toml             # 项目配置
├── .env                       # 环境变量
├── core/                      # 核心业务逻辑
│   ├── server.py              # WebSocket 服务器
│   └── assistant.py           # AI 对话和代码生成
├── gui/                       # GUI 界面
│   ├── main_window.py         # 主窗口
│   ├── model_manager.py       # 模型管理
│   ├── widgets/               # UI 组件
│   └── tabs/                  # Tab 模块
├── utils/                     # 工具层
│   ├── config.py              # 配置读写
│   ├── input_simulator.py     # 键盘模拟
│   └── extension_setup.py     # 扩展加载
└── chrome/chrome/             # Chrome 扩展
    ├── manifest.json          # 扩展配置
    ├── background.js          # Service Worker
    ├── content.js             # Content Script
    └── content.css            # 扩展样式
```

## 支持的平台

- 头歌 Educoder（educoder.net）
- 力扣 LeetCode（leetcode.cn）
- 牛客网（nowcoder.com）
- yhsun.cn OJ 平台

## 开发指南

### 添加新语言

在 `gui/language_manager.py` 的默认语言列表中添加。

### 自定义 AI 提示词

编辑 `core/assistant.py` 中的 `GENERATION_RULES` 和 `REVISION_RULES`。

### 扩展支持的编辑器

在 `chrome/chrome/content.js` 中添加新的编辑器适配逻辑。

## 许可证

MIT License