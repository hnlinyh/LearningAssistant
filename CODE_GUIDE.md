# 学习助手 - 代码修改指南

## 项目架构总览

```python
# 正常生成模式（6条规则）
你是一个专业的编程助手，负责生成{lang_name}代码。
重要规则：
1. 只返回纯代码，不要有任何解释、注释或额外文字
2. 绝对不要使用任何代码块标记
3. 代码必须完整且可运行，包括导入的库和模块等
4. 如果用户提供了已有代码，已有代码是不可改动的既有内容，严格保留
5. 如果用户提供了已有代码，只能在原有代码基础上补充缺失部分
6. 必须返回完整最终代码文件

# 纠错模式（5条规则）
你是一个专业的编程助手，负责根据测试失败信息修正{lang_name}代码。
重要规则：
1. 只返回纯代码，不要有任何解释、注释或额外文字
2. 绝对不要使用任何代码块标记
3. 代码必须完整且可运行，包括导入的库和模块等
4. 必须返回完整最终代码文件，不能只返回局部补丁
5. 专注于修复已知的错误，确保代码通过所有测试
```
main.py                          # 入口：初始化环境、启动主窗口
├── path_config.py               # 路径常量
├── gui/
│   ├── themes.py                # 统一颜色常量（PRIMARY, BG, BORDER 等）
│   ├── main_window.py           # 主窗口（薄编排层：Tab创建、托盘、生命周期）
│   ├── model_manager.py         # AI模型获取与测试
│   ├── language_manager.py      # 编程语言列表管理
│   ├── extension_dialog.py      # 浏览器扩展安装弹窗
│   ├── update_window.py         # 版本更新检查弹窗
│   ├── input_test.py            # 基础输入测试弹窗
│   ├── advanced_input_test.py   # 高级输入测试弹窗
│   ├── widgets/                 # 可复用UI组件
│   │   ├── log_panel.py         # 日志面板组件（LogPanel）
│   │   └── section_textbox.py   # 带标签文本框组件（SectionTextbox）
│   └── tabs/                    # 独立Tab模块
│       └── input_tab.py         # 桌面输入Tab（题目显示、代码生成、键盘模拟）
├── core/
│   ├── server.py                # WebSocket服务器管理
│   └── assistant.py             # AI对话逻辑、代码生成、消息处理
└── utils/
    ├── config.py                # .env 和 config.ini 配置读写
    ├── input_simulator.py       # 键盘鼠标模拟、粘贴
    └── extension_setup.py       # Chrome/Edge扩展加载、单实例锁
```

---

## 快速定位索引

**告诉 AI：「我要修改 ___」**

| 要修改的内容 | 只读这些文件 |
|-------------|------------|
| 颜色/主题常量 | `gui/themes.py` |
| 应用启动流程、环境变量加载 | `main.py` |
| 项目路径配置常量 | `path_config.py` |
| 主窗口整体布局、Tab创建 | `gui/main_window.py` |
| 桌面输入Tab UI / 生成代码 / 复制粘贴 / 输入测试 | `gui/tabs/input_tab.py` |
| 日志面板组件 | `gui/widgets/log_panel.py` |
| 带标签文本框组件 | `gui/widgets/section_textbox.py` |
| AI 模型 Tab 的 UI / 获取模型 / 测试模型 | `gui/main_window.py` + `gui/model_manager.py` |
| 运行配置 Tab 的 UI / 扩展安装按钮 | `gui/main_window.py` + `gui/extension_dialog.py` |
| 服务器 Tab 的 UI / 启停服务器 | `gui/main_window.py` + `core/server.py` |
| WebSocket 消息分发逻辑 | `core/server.py` 的 `_handler()` + `core/assistant.py` 的 `server()` |
| **AI 代码生成 Prompt / 纠错逻辑** | `core/assistant.py` 的 `get_complete_code_solution()` |
| AI Prompt 系统指令 | `core/assistant.py` 的 `_get_system_prompt()`（正常生成6条规则 / 纠错5条规则） |
| 键盘模拟 / 粘贴逻辑 | `utils/input_simulator.py` |
| 配置保存到 .env / 从 .env 加载 | `utils/config.py` |
| 浏览器扩展自动加载 (Selenium) | `utils/extension_setup.py` 的 `launch_with_extension_selenium()` |
| 浏览器扩展手动安装引导 UI | `gui/extension_dialog.py` |
| 版本更新检查逻辑 | `gui/update_window.py` |
| 语言管理弹窗 UI | `gui/language_manager.py` |
| 基础输入测试弹窗 | `gui/input_test.py` |
| 高级输入测试弹窗 | `gui/advanced_input_test.py` |
| 系统托盘功能 | `gui/main_window.py` 的 `_setup_tray()` / `_on_close()` |
| 主窗口日志显示 | `gui/widgets/log_panel.py` 的 `LogPanel` |
| 端口配置 UI | `gui/main_window.py` 的 `_adjust_port()` / `_start_server()` |
| 窗口关闭行为（最小化托盘） | `gui/main_window.py` 的 `_on_close()` |

---

## 完整业务逻辑

### 1. 应用启动流程

```
main.py: main()
  ├─ logging.basicConfig()         # 初始化日志（控制台 + 文件）
  ├─ ensure_env()                  # 检查 .env 是否存在，不存在则直接创建默认配置
  ├─ load_dotenv()                 # 加载 .env 环境变量
  ├─ ctk.set_appearance_mode()     # 设置外观模式（light/dark）
  ├─ ctk.set_default_color_theme() # 设置默认颜色主题
  └─ MainWindow()                  # 创建主窗口
       ├─ _build_ui()              # 构建UI（Header、Tabview、LogPanel、Footer）
       │    ├─ 创建 Header Canvas（渐变背景 + 标题）
       │    ├─ 创建 Tabview（4个Tab）
       │    │    ├─ "AI 模型" Tab
       │    │    ├─ "桌面输入" Tab → InputTab 组件
       │    │    ├─ "运行配置" Tab
       │    │    └─ "服务器" Tab
       │    ├─ 创建 LogPanel 日志面板
       │    └─ 创建 Footer 链接
       ├─ _load_config_from_env()  # 从 .env 加载配置到GUI控件
       └─ _setup_tray()            # 初始化系统托盘
```

**关键逻辑**：
- 应用启动时自动检查 `.env` 文件，不存在则直接创建包含默认配置的新文件
- 通过 `load_dotenv()` 加载环境变量（API Key、Base URL、Model、WS Port）
- 主窗口初始化时从 `.env` 读取配置并填充到GUI控件
- 用户修改配置时自动保存到 `.env`（通过 `selected_model.trace_add` 监听）

---

### 2. AI 模型管理业务逻辑

**获取模型列表流程**：
```
用户点击"获取模型"按钮
  └─ MainWindow._fetch_models()
       ├─ 读取 API Key 和 Base URL
       ├─ _save_config_to_env()     # 先保存配置
       └─ 启动后台线程 _fetch_models_thread()
            └─ ModelManager(gui).fetch_models(api_key, base_url)
                 └─ AsyncOpenAI(api_key, base_url).models.list()
                      └─ 返回所有模型的 id 列表
            └─ _update_model_list(models)
                 └─ 清空 model_list_frame
                 └─ 为每个模型创建 CTkRadioButton
                 └─ 保留已选中的模型（即使不在新列表中）
```

**测试模型流程**：
```
用户点击"测试选中模型"按钮
  └─ MainWindow._test_model()
       └─ 启动后台线程 _test_model_thread()
            └─ ModelManager(gui).test_model(api_key, base_url, model_name)
                 └─ AsyncOpenAI().chat.completions.create()
                      ├─ model=model_name
                      ├─ messages=[{"role": "user", "content": "Say OK"}]
                      ├─ max_tokens=10
                      └─ temperature=0
                 └─ 计算延迟 latency = time.time() - start
                 └─ 返回 {success: bool, latency: float, error: str}
            └─ _show_test_result(model, result)
                 └─ 成功：显示 ✅ 和延迟时间
                 └─ 失败：显示 ❌ 和错误信息
```

**模型筛选逻辑**：
```
用户在筛选框输入关键词
  └─ MainWindow._filter_models()
       └─ 清空 model_list_frame
       └─ 过滤 model_list（不区分大小写）
       └─ 重新渲染过滤后的模型单选按钮

用户选中模型
  └─ _on_model_selected()
       ├─ 清空筛选框
       ├─ 在筛选框中显示选中的模型名
       └─ _save_config_to_env()     # 自动保存配置
```

---

### 3. WebSocket 服务器业务逻辑

**启动服务器流程**：
```
用户点击"启动服务器"按钮
  └─ MainWindow._start_server()
       ├─ _save_config_to_env()     # 保存当前配置
       ├─ 读取端口（从 ws_port_entry 或环境变量）
       ├─ 构建 model_info 字典（包含 model、api_key、base_url）
       ├─ 创建 ServerManager(self, model_info, port=ws_port)
       └─ ServerManager.start()
            └─ 在新线程中运行 _run_server()
                 └─ asyncio.new_event_loop()
                 └─ _start_websocket_server()
                      ├─ 创建 LearningAssistant(gui, model_info)
                      └─ websockets.serve(_handler, host, port)
                           ├─ ping_interval=20
                           ├─ ping_timeout=60
                           └─ process_request=_process_request（处理 /discover 请求）
       ├─└─ 更新UI状态（绿色指示灯、服务器运行中标签）
       └─ 写入 server-config.json 到扩展目录（包含 ws_port、ws_url、ocr_api_url）：
            ├─ ws_port: 端口号
            ├─ ws_url: WebSocket 地址
            └─ ocr_api_url: 'https://ocr.yhsun.cn/'
```

**停止服务器流程**：
```
用户点击"停止服务器"按钮
  └─ MainWindow._stop_server()
       └─ ServerManager.stop()
            ├─ server_running = False
            └─ assistant.reset()   # 重置状态
       └─ 更新UI状态（红色指示灯、服务器未运行标签）
```

**HTTP 发现接口**：
```
浏览器扩展访问 http://localhost:8000/discover
  └─ ServerManager._process_request()
       └─ 返回 JSON: {"ws_port": 8000, "ws_url": "ws://localhost:8000"}
```

**WebSocket 连接处理**：
```
浏览器扩展连接 WebSocket
  └─ ServerManager._handler(websocket)
       └─ LearningAssistant.server(websocket)
            ├─ 发送 config_info 消息（模型名称）
            └─ 循环接收消息
                 └─ 根据 msg_type 分发到不同 handler
```

---

### 4. AI 代码生成业务逻辑

**生成代码完整流程**：
```
浏览器扩展发送题目（content_auto_input 或 manual_question）
  └─ LearningAssistant.handle_content_auto_input()
       ├─ 提取 question、current_code、language、sync_question
       ├─ 更新 current_language
       ├─ 根据 sync_question 标志位决定是否调用 gui.set_question(question)
       ├─ 发送 server_ack 消息（status: processing）
       └─ get_complete_code_solution(question, current_code)
            ├─ 检查 client 是否初始化（API Key 是否存在）
            ├─ 构建 prompt：
       │    ├─ 题目要求
       │    ├─ 已有代码（如有，标注"不可修改"）
       │    └─ 生成指令（有已有代码时提示"在已有代码基础上补充"，无已有代码时提示"生成完整代码"）
            ├─ 尝试 2 次 API 调用：
            │    ├─ 第1次：temperature=0.3
            │    └─ 第2次：temperature=0（更确定性）
            │    └─ 调用 client.chat.completions.create()
            │         ├─ model=model_name
            │         ├─ messages=[system_prompt, user_prompt]
            │         ├─ max_tokens=8192
            │         └─ stream=False
            │    └─ clean_code_response(raw_content)  # 清理代码块标记
            │    └─ _is_complete_code(code, existing_code)  # 完整性检查
            │    └─ 如果通过，返回代码
            └─ 返回 code 或 None
       └─ 如果代码生成成功：
            └─ 发送 code_solution 消息（code, language, model_used）
       └─ 如果失败：
            └─ 发送 error 消息
```

**代码清理逻辑**：
```
clean_code_response(content)
  ├─ 如果内容为空，返回 ''
  ├─ 正则匹配 ```语言\n代码\n``` 块
  ├─ 如果有匹配，返回最长的代码块
  └─ 如果没有匹配，返回去掉注释行（#、//、<!--）的内容
```

**代码完整性检查**：
```
_is_complete_code(code, existing_code)
  ├─ 代码为空或长度 < 20 字符 → False
  └─ 其他情况 → True
```

---

### 5. AI 代码纠错业务逻辑

**纠错触发条件**：
```
浏览器扩展发送测试结果（test_results）
  └─ LearningAssistant.handle_test_results()
       ├─ 解析 results.text
       ├─ 检查是否包含失败关键词：
       │    [failed], 错误, 失败, error, fail
       └─ 如果有失败：
            └─ get_complete_code_solution(question, current_code, test_text)
                 ├─ 构建 prompt（纠错模式）：
       │    ├─ 题目要求
       │    ├─ 已有代码
       │    ├─ 测试失败信息
       │    └─ 修复指令（"请根据测试失败信息修复代码中的错误，返回完整修复后的代码"）
                 ├─ 调用 _get_system_prompt(has_test_failure=True)
                 │    └─ 返回纠错专用系统提示词
                 ├─ 尝试 2 次 API 调用：
                 │    ├─ temperature=0.3/0
                 │    └─ 调用 client.chat.completions.create()
                 │    └─ clean_code_response() 清理
                 │    └─ _is_complete_code() 完整性检查
                 └─ 返回修订代码 或 None
            └─ 如果修订成功：
                 └─ 发送 code_revision 消息（code）
            └─ 如果失败：
                 └─ 发送 error 消息
       └─ 如果没有失败：
            └─ 发送 test_results_response（所有测试通过）
```

**代码生成功能复用**：
- `get_complete_code_solution()` 同时支持代码生成和纠错场景
- 通过 `test_failure` 参数区分：为空时为正常生成，非空时为纠错模式
- `_get_system_prompt()` 根据 `has_test_failure` 参数返回不同的系统提示词
- 无重试计数限制，用户可多次触发纠错

---

### 6. 桌面输入业务逻辑

**复制代码**：
```
用户点击"复制代码"按钮
  └─ InputTab._copy_code()
       ├─ 获取 input_content_text 内容
       ├─ 检查内容有效（非空且非"生成失败"提示）
       ├─ clipboard_clear()
       ├─ clipboard_append(code)
       └─ 日志："代码已复制到剪贴板"
```

**模拟键盘输入**：
```
用户点击"模拟键盘输入"按钮
  └─ InputTab._input_test()
       ├─ 获取 input_content_text 内容
       ├─ 检查内容非空
       ├─ _validate_test_params()  # 验证参数
       │    ├─ 解析 wait_time 和 interval
       │    └─ 检查非负数
       ├─ 日志："输入测试将在 X 秒后开始"
       └─ 启动后台线程 _input_test_thread()
            ├─ 倒计时循环（wait_time 秒）
            │    └─ 每秒更新日志
            ├─ 如果启用特殊字符处理：
            │    └─ 替换 \n → 换行，\t → 制表符
            ├─ input_simulator.reset()
            ├─ input_simulator.typing_active = True
            └─ 逐行输入循环：
                 ├─ 检查 typing_active（ESC 中断）
                 ├─ input_simulator._write_text(line)
                 ├─ 如果不是最后一行：
                 │    └─ input_simulator._press_key('enter')
                 ├─ 计算进度百分比
                 ├─ 更新日志
                 └─ time.sleep(interval)
            └─ 日志："模拟键盘输入完成"
```

---

### 7. 键盘模拟底层实现

**文本写入策略**：
```
InputSimulator._write_text(text)
  ├─ 如果是 Linux 且有 xdotool：
  │    └─ 逐字符调用 xdotool type --delay 1 char
  └─ 其他情况：
       ├─ 优先使用 keyboard.write(text)
       └─ 失败则回退到：
            ├─ pyperclip.copy(text)
            └─ pyautogui.hotkey('ctrl', 'v')
```

**按键策略**：
```
InputSimulator._press_key(key)
  ├─ 如果是 Linux 且有 xdotool：
  │    └─ xdotool key key
  └─ 其他情况：
       ├─ 优先使用 keyboard.press_and_release(key)
       └─ 失败则回退到 pyautogui.press(key)
```

**粘贴代码流程**：
```
InputSimulator.paste_code(code)
  ├─ _install_esc_hook()  # 注册 ESC 键监听
       ├─ pyautogui.click(屏幕中心)  # 确保焦点在目标窗口
       ├─ time.sleep(0.3)
       ├─ _clear_editor_before_input()
       │    ├─ pyautogui.hotkey('ctrl', 'a')  # 全选
       │    ├─ time.sleep(0.1)
       │    ├─ pyautogui.press('delete')      # 删除
       │    └─ time.sleep(0.1)
       ├─ time.sleep(0.2)
  ├─ pyperclip.copy(code)               # 复制到剪贴板
  ├─ pyautogui.hotkey('ctrl', 'v')      # 粘贴
  ├─ time.sleep(0.5)
  └─ _remove_esc_hook()                 # 移除 ESC 监听
```

**逐字输入流程**：
```
InputSimulator.simulate_typing(text, delay, on_progress)
  ├─ _install_esc_hook()
       ├─ pyautogui.click(屏幕中心)
       ├─ time.sleep(0.3)
       ├─ _clear_editor_before_input()
       │    ├─ pyautogui.hotkey('ctrl', 'a')  # 全选
       │    ├─ time.sleep(0.1)
       │    ├─ pyautogui.press('delete')      # 删除
       │    └─ time.sleep(0.1)
       ├─ time.sleep(0.2)
  └─ 逐行循环：
       ├─ 检查 esc_pressed 或 typing_active
       │    └─ 如果中断，返回 False
       ├─ _write_text(line)
       ├─ 如果不是最后一行：
       │    └─ _press_key('enter')
       ├─ 调用 on_progress(进度百分比)
       └─ time.sleep(delay)
  └─ _remove_esc_hook()
  └─ 返回 True
```

**ESC 中断机制**：
```
_install_esc_hook()
  └─ keyboard.on_press_key('esc', lambda _: _on_esc())

_on_esc()
  ├─ esc_pressed = True
  └─ typing_active = False

_remove_esc_hook()
  └─ keyboard.unhook_key('esc')
```

---

### 8. 浏览器扩展管理业务逻辑

**扩展安装引导**：
```
用户点击"安装浏览器扩展"按钮
  └─ MainWindow._show_extension_dialog()
       └─ ExtensionInstallDialog(parent)
            ├─ 显示安装说明（为什么需要扩展）
            ├─ 手动安装区域：
            │    ├─ "打开 Chrome 扩展管理" → _open_chrome_ext()
            │    ├─ "打开 Edge 扩展管理" → _open_edge_ext()
            │    └─ "打开扩展文件夹" → _open_ext_folder()
            └─ 启动浏览器区域：
                 ├─ "启动 Chrome" → _launch_browser('chrome')
                 └─ "启动 Edge" → _launch_browser('edge')
```

**浏览器启动流程**：
```
ExtensionSetup.launch_with_extension(browser, url)
  ├─ _acquire_single_instance_lock()  # 防止重复启动
  │    └─ 绑定端口 48573 的 socket
  │    └─ 如果端口被占用，返回 False 并提示 "已有浏览器实例在运行，请先关闭"
  └─ 优先尝试 Selenium 模式：
       └─ launch_with_extension_selenium()
            ├─ 查找扩展目录（包含 manifest.json）
            ├─ 复制到临时目录（避免中文路径问题）
            ├─ 创建 ChromeOptions/EdgeOptions
            │    ├─ --load-extension=临时目录
            │    ├─ --disable-extensions-except=临时目录
            │    ├─ --start-maximized
            │    ├─ --disable-gpu
            │    ├─ --no-sandbox
            │    └─ excludeSwitches: enable-automation, enable-logging
            ├─ 使用 Selenium Manager 自动下载匹配的 driver
            └─ webdriver.Chrome(options) 或 webdriver.Edge(options)
                 └─ driver.get(url 或 'https://www.educoder.net/')
       └─ 如果 Selenium 未安装或失败：
            └─ launch_with_extension_simple()
                 └─ 命令行启动：
                      ├─ chrome --load-extension=临时目录
                      └─ 附加 --no-first-run --no-default-browser-check
                 └─ 如果 Chrome 未找到，自动尝试 Edge
                 └─ 如果都未找到，返回错误信息
```

**浏览器路径查找**：
```
get_chrome_path()
  ├─ Windows：
  │    ├─ %ProgramFiles%\Google\Chrome\Application\chrome.exe
  │    ├─ %ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
  │    ├─ %LocalAppData%\Google\Chrome\Application\chrome.exe
  │    └─ 注册表 App Paths 查找
  ├─ macOS：
  │    └─ /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
  └─ Linux：
       ├─ /usr/bin/google-chrome
       ├─ /usr/bin/chromium-browser
       └─ /usr/bin/chromium
```

**扩展目录查找**：
```
get_extension_dir()
  ├─ 搜索路径列表：
  │    ├─ self.extension_path（CHROME_EXTENSION_PATH）
  │    ├─ 上级目录/chrome
  │    ├─ 当前工作目录/chrome/chrome
  │    └─ 当前工作目录/chrome
  └─ 检查每个路径下是否存在 manifest.json│    └─ 返回第一个匹配的路径
```

---

### 10. 配置同步与广播业务逻辑

**配置同步请求**：
```
扩展端发送 sync_input_config 消息
  └─ LearningAssistant.handle_sync_input_config(websocket, data)
       ├─ 提取 config 字典
       └─ broadcast_to_clients({type: "sync_input_config", config})
            └─ 遍历 connected_clients 集合
                 ├─ 向每个客户端发送消息
                 └─ 清理断开的连接
```

**广播机制**：
```
ServerManager.broadcast_config(config)
  └─ 获取 _server_loop（服务器事件循环）
  └─ asyncio.run_coroutine_threadsafe(
       assistant.broadcast_to_clients({type: "sync_input_config", config}),
       loop
     )
```

**桌面端保存配置**：
```
InputTab._save_config()
  ├─ 验证参数（wait_time、interval）
  ├─ 构建 config 字典
  ├─ 通过 mw.server_manager.broadcast_config(config) 广播
  └─ 日志："配置已保存并同步到扩展端"
```

---

### 11. 新增方法补充

**assistant.py 新增方法**：

| 方法 | 做什么 |
|-----|-------|
| `handle_sync_input_config(websocket, data)` | 处理扩展端配置同步请求，广播到所有客户端 |
| `broadcast_to_clients(message)` | 向所有连接的 WebSocket 客户端广播消息，自动清理断开连接 |
| `generate_code_for_gui(question, existing_code)` | 供 GUI 直接调用代码生成，包装 get_complete_code_solution |
| `type_text(text)` | 直接输入文本（3秒倒计时后粘贴），供 InputSimulator 使用 |

**extension_setup.py 补充**：

| 方法 | 做什么 |
|-----|-------|
| `_acquire_single_instance_lock()` | 绑定端口 48573 防止重复启动，失败返回 False 并提示 "已有浏览器实例在运行" |
| `_release_single_instance_lock()` | 释放单实例锁 |
| `get_chrome_version()` | 通过注册表或命令行获取 Chrome 版本号 |
| `get_edge_version()` | 通过注册表获取 Edge 版本号 |
| `open_chrome_extensions()` | 打开 Chrome 扩展管理页面 |
| `open_edge_extensions()` | 打开 Edge 扩展管理页面 |
| `open_extension_folder()` | 打开扩展文件夹（explorer/open/xdg-open） |

---

### 9. 配置持久化业务逻辑

**保存到 .env**：
```
MainWindow._save_config_to_env()
  └─ 从 GUI 控件读取：
       ├─ api_key_entry.get() → OPENAI_API_KEY
       ├─ api_url_entry.get() → OPENAI_BASE_URL
       ├─ selected_model.get() → OPENAI_MODEL
       └─ ws_port_entry.get() → WS_PORT
  └─ ConfigManager.save_to_env(data)
       ├─ 读取现有 .env 文件
       ├─ 解析已有键值对
       ├─ 更新已有键的值（保留注释）
       ├─ 新键追加到文件末尾
       └─ 写回文件
```

**从 .env 加载**：
```
MainWindow._load_config_from_env()
  └─ ConfigManager.load_from_env()
       └─ 读取 .env 文件
       └─ 解析键值对（跳过注释和空行）
       └─ 返回字典
  └─ 填充到 GUI 控件：
       ├─ api_key_entry.insert(0, api_key)
       ├─ api_url_entry.insert(0, base_url)
       ├─ selected_model.set(model)
       └─ ws_port_entry.insert(0, ws_port)
```

**自动保存机制**：
```
MainWindow.__init__()
  └─ selected_model.trace_add('write', lambda *_: _save_config_to_env())
       └─ 用户选择模型时自动保存
  └─ _on_model_selected()
       └─ 清空筛选框 + 显示选中模型 + 保存配置
```

---

### 10. 系统托盘业务逻辑

**托盘初始化**：
```
MainWindow._setup_tray()
  ├─ 创建 64x64 纯色图标（PRIMARY 颜色）
  ├─ 定义菜单项：
  │    ├─ "显示" → on_show() → icon.stop() + self.deiconify()
  │    └─ "退出" → on_quit() → icon.stop() + self.destroy()
  └─ 创建 pystray.Icon
  └─ 绑定 WM_DELETE_WINDOW 协议到 _on_close()
```

**窗口关闭行为**：
```
MainWindow._on_close()
  ├─ 如果 config_minimize_tray 为真 且 tray_icon 存在：
  │    ├─ self.withdraw()  # 隐藏窗口
  │    └─ 启动托盘线程：tray_icon.run()
  └─ 否则：
       ├─ 如果服务器运行：_stop_server()
       └─ self.destroy()  # 退出应用
```

---

### 11. 日志系统业务逻辑

**日志配置**（main.py）：
```
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
  handlers=[
    logging.StreamHandler(),                    # 控制台输出
    logging.FileHandler('learning_assistant.log') # 文件输出
  ]
)
```

**GUI 日志显示**：
```
LogPanel.log_message(msg)
  ├─ 添加时间戳：HH:MM:SS
  └─ 线程安全写入：
       ├─ 如果在主线程：直接更新
       └─ 如果在后台线程：self.after(0, _update)
  └─ 自动滚动到末尾：self.log_text.see('end')
```

---

### 12. 语言管理业务逻辑

**语言列表管理**：
```
LanguageManager.__init__()
  ├─ 初始化内置语言列表：
  │    [C, C++, Java, Python, JavaScript, C#]
  └─ _load_custom()
       └─ 从 config.ini 读取 custom_languages
       └─ 合并到语言列表

添加语言：
  └─ add_language(name)
       ├─ 检查名称非空且不在列表中
       ├─ 添加到列表
       └─ _save_custom() → 保存到 config.ini

删除语言：
  └─ remove_language(name)
       ├─ 检查不是内置语言
       ├─ 从列表移除
       └─ _save_custom() → 保存到 config.ini
```

---

### 13. 版本更新检查业务逻辑

```
UpdateWindow.__init__()
  └─ 启动后台线程 _check_update()
       └─ requests.get(GitHub API latest release)
            ├─ 如果成功：
            │    ├─ 比较最新版本与 CURRENT_VERSION
            │    ├─ 如果有新版本：
            │    │    ├─ 显示新版本号
            │    │    ├─ 显示更新日志
            │    │    └─ 启用"立即更新"按钮
            │    └─ 如果已是最新：
            │         └─ 显示"已是最新版本"
            └─ 如果失败：
                 └─ 显示"检查更新失败"或"网络错误"
```

---

## 文件详细说明

### `gui/themes.py`

**职责**：统一管理所有颜色常量，消除各文件重复定义

**导出常量**：

| 常量 | 值 | 用途 |
|-----|---|-----|
| `PRIMARY` | `#4F6BED` | 主色调（按钮、链接） |
| `PRIMARY_DARK` | `#3B52CC` | 深色主色调（悬停） |
| `PRIMARY_LIGHT` | `#E8EDFD` | 浅色主色调（下拉项悬停） |
| `SUCCESS` | `#10B981` | 成功色 |
| `WARNING` | `#F59E0B` | 警告色 |
| `ERROR` | `#EF4444` | 错误色 |
| `SURFACE` | `#FFFFFF` | 表面色（卡片背景） |
| `BG` | `#F8FAFC` | 背景色 |
| `TEXT_PRIMARY` | `#1E293B` | 主文字色 |
| `TEXT_SECONDARY` | `#64748B` | 次文字色 |
| `BORDER` | `#E2E8F0` | 边框色 |

**使用方式**：`from gui.themes import *`

---

### `main.py`

**职责**：应用入口，初始化日志，加载 `.env`，创建主窗口

**关键函数**：

| 函数 | 做什么 |
|-----|-------|
| `logging.basicConfig()` | 初始化日志系统，输出到控制台和 `learning_assistant.log` 文件 |
| `ensure_env()` | 检查 `.env` 是否存在，不存在则直接创建包含默认配置的新文件 |
| `main()` | 加载 dotenv，设置 CTkinter 外观，创建 `MainWindow` 并进入事件循环 |

---

### `path_config.py`

**职责**：定义项目全局路径常量，管理 sys.path

**关键逻辑**：
- 在模块导入时自动将 `PROJECT_ROOT` 插入 `sys.path` 首位，确保其他模块可以正确导入

**导出常量**：

| 常量 | 值 | 用途 |
|-----|---|-----|
| `PROJECT_ROOT` | `main.py` 所在目录 | 项目根目录 |
| `CHROME_EXTENSION_PATH` | `PROJECT_ROOT/chrome/chrome` | 浏览器扩展目录 |
| `LOG_DIR` | `PROJECT_ROOT/logs` | 日志目录 |
| `CONFIG_DIR` | `~/.learning_assistant` | 用户配置目录 |

---

### `gui/main_window.py`

**职责**：主窗口薄编排层，聚合各Tab组件、配置持久化、托盘管理

**关键类**：`MainWindow` (customtkinter.CTk)

**关键属性**：

| 属性 | 类型 | 用途 |
|-----|------|------|
| `input_tab` | `InputTab` | 桌面输入Tab组件 |
| `log_panel` | `LogPanel` | 日志面板组件 |
| `server_running` | `bool` | 服务器运行状态 |
| `server_manager` | `ServerManager` | WebSocket服务器管理器 |
| `selected_model` | `StringVar` | 当前选中的AI模型 |
| `selected_language` | `StringVar` | 当前选中的编程语言 |

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `_build_ui()` | 构建整体 UI（Header、Tabview、LogPanel、Footer） |
| `_build_model_tab()` | AI 模型 Tab UI |
| `_build_config_tab()` | 运行配置 Tab UI |
| `_build_server_tab()` | 服务器 Tab UI |
| `log_message(msg)` | 委托给 `log_panel.log_message()` |
| `set_question(question)` | 更新输入内容框（线程安全，供 assistant.py 调用） |
| `set_code(code)` | 更新输入内容框（线程安全，供 assistant.py 调用） |
| `_fetch_models()` | 获取模型列表（调用 ModelManager 实例方法） |
| `_test_model()` | 测试选中模型（调用 ModelManager 实例方法） |
| `_start_server()` | 启动 WebSocket 服务器 |
| `_stop_server()` | 停止服务器 |
| `_launch_browser()` | 启动浏览器 |
| `_setup_tray()` | 初始化系统托盘图标 |
| `_on_close()` | 窗口关闭事件 |
| `_save_config_to_env()` | 从 GUI 控件读取配置保存到 .env |
| `_load_config_from_env()` | 从 .env 加载配置到 GUI 控件 |

---

### `gui/tabs/input_tab.py`

**职责**：桌面输入Tab的UI和业务逻辑，包括复制代码、模拟键盘输入

**关键类**：`InputTab` (customtkinter.CTkFrame)

**构造函数**：`InputTab(master, main_window)` — `main_window` 为 MainWindow 引用

**UI组件**：

| 组件 | 类型 | 用途 |
|-----|------|------|
| `input_content_text` | `CTkTextbox` | 输入内容面板（可编辑） |
| `lang_menu` | `CTkOptionMenu` | 编程语言选择器 |
| `input_wait_time_var` | `StringVar` | 等待时间参数 |
| `input_interval_var` | `StringVar` | 输入间隔参数 |
| `input_special_char_var` | `BooleanVar` | 特殊字符处理开关 |
| `cancel_btn` | `CTkButton` | 取消输入按钮（输入时启用，完成后禁用） |

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `_copy_code()` | 复制代码到剪贴板 |
| `_input_test()` | 模拟键盘输入（带倒计时逐行输入） |
| `_input_test_thread(text, wait_time, interval)` | 后台线程执行逐行输入，带进度更新和 ESC 中断支持 |
| `_cancel_input()` | 取消输入，设置 `typing_active = False` |
| `_save_config()` | 保存输入配置并广播到扩展端 |
| `_validate_test_params()` | 验证等待时间和输入间隔参数 |

---

### `gui/widgets/log_panel.py`

**职责**：可复用的日志显示面板

**关键类**：`LogPanel` (customtkinter.CTkFrame)

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `log_message(msg)` | 线程安全的日志写入，自动添加 HH:MM:SS 时间戳 |
| `clear()` | 清空日志内容 |

---

### `gui/widgets/section_textbox.py`

**职责**：带标签的文本框组件，支持只读/编辑模式

**关键类**：`SectionTextbox` (customtkinter.CTkFrame)

**构造函数**：`SectionTextbox(master, label_text="内容", height=100, read_only=False)`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `set_content(text)` | 替换全部内容（线程安全） |
| `get_content()` | 返回当前内容 |
| `clear()` | 清空内容 |
| `set_read_only(flag)` | 切换只读状态 |

---

### `core/server.py`

**职责**：WebSocket 服务器管理，接收浏览器扩展连接

**关键类**：`ServerManager`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `start()` | 在新线程中启动 WebSocket 服务器 |
| `stop()` | 停止服务器，重置 assistant 状态 |
| `_handler()` | 接收客户端连接，调用 `assistant.server()` 处理消息 |
| `_process_request()` | 处理 HTTP 发现请求（/discover），返回 ws_port 和 ws_url |
| `_start_websocket_server()` | 创建 LearningAssistant 实例，启动 websockets.serve |
| `update_model()` | 通知 assistant 更新模型配置 |
| `set_language()` | 通知 assistant 更新语言设置 |
| `broadcast_config()` | 通过事件循环广播配置到所有连接的客户端 |

**通信流程**：
```
浏览器扩展 → WebSocket → _handler() → assistant.server() → 各 handle_* 方法
```

---

### `core/assistant.py`

**职责**：AI 核心逻辑，消息处理，代码生成

**关键类**：`LearningAssistant`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `__init__(gui, model_info)` | 初始化 client、input_simulator、状态变量 |
| `server()` | **消息分发中心**，根据 `msg_type` 分发到不同 handler |
| `handle_content_auto_input()` | 处理题目内容 → 生成代码 → 返回 `code_solution`，根据 `sync_question` 标志决定是否调用 `gui.set_question()` 更新桌面端 |
| `handle_test_results()` | 处理测试失败 → 纠错 → 返回 `code_revision`，同时调用 `gui.set_code()` 同步纠错后代码 |
| `handle_ready_for_input()` | 将代码粘贴到编辑器 |
| `handle_sync_code()` | 接收扩展同步的代码，调用 `gui.set_code()` 显示到桌面端 |
| `handle_simulate_input()` | 处理扩展端的模拟键盘输入请求，带倒计时和进度更新 |
| `handle_cancel_input()` | 处理取消输入请求，设置 `typing_active = False` |
| `handle_sync_input_config()` | 处理配置同步请求，通过 `broadcast_to_clients()` 广播到所有客户端 |
| `broadcast_to_clients()` | 向所有连接的 WebSocket 客户端广播消息，自动清理断开连接 |
| `generate_code_for_gui()` | 供 GUI 直接调用的代码生成入口 |
| `get_complete_code_solution()` | **AI 代码生成主函数**，同时支持代码生成和纠错场景 |

**消息类型处理**（在 `server()` 方法中）：

| msg_type | 调用的 handler | 说明 |
|---------|---------------|------|
| `content_auto_input` | `handle_content_auto_input()` | 扩展自动提取题目 |
| `manual_question` | `handle_content_auto_input()` | 手动输入题目 |
| `test_results` | `handle_test_results()` | 测试结果（失败触发纠错） |
| `ready_for_input` | `handle_ready_for_input()` | 编辑器就绪，准备粘贴 |
| `direct_input_complete` | `handle_direct_input_complete()` | 扩展端直接写入完成 |
| `progress_request` | `send_progress_update()` | 请求进度 |
| `set_language` | `set_language()` | 设置语言 |
| `sync_code` | `handle_sync_code()` | 同步代码到桌面端 |
| `simulate_input` | `handle_simulate_input()` | 扩展端请求模拟键盘输入 |
| `cancel_request` | `handle_cancel_input()` | 取消输入请求 |
| `sync_input_config` | `handle_sync_input_config()` | 配置同步请求，广播到所有客户端 |

---

### `gui/model_manager.py`

**职责**：AI 模型列表获取与测试

**关键类**：`ModelManager`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `fetch_models(api_key, base_url)` | 调用 `/models` API 获取模型列表（异步实例方法） |
| `test_model(api_key, base_url, model_name)` | 测试模型连通性，返回 `{success, latency, error}`（异步实例方法） |
| `filter_models(keyword)` | 按关键词过滤模型 |

---

### `gui/language_manager.py`

**职责**：编程语言列表管理

**关键类**：`LanguageManager` + `LanguageManagerDialog`

**内置语言**：`C`, `C++`, `Java`, `Python`, `JavaScript`, `C#`

---

### `gui/extension_dialog.py`

**职责**：浏览器扩展安装引导弹窗 UI

---

### `utils/input_simulator.py`

**职责**：键盘鼠标模拟，实现代码粘贴和逐字输入

**关键类**：`InputSimulator`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `paste_code()` | **主入口**：安装 ESC 钩子 → 点击屏幕中心 → 清空编辑器（Ctrl+A → Delete） → 复制到剪贴板 → Ctrl+V 粘贴 → 移除 ESC 钩子 |
| `simulate_typing()` | 逐字/逐行输入（带进度回调，ESC 可中断） |
| `type_text()` | 直接粘贴（3秒倒计时 → 复制+Ctrl+V，失败回退 keyboard.write） |
| `_write_text()` | 写文本（底层方法） |
| `_press_key()` | 按键（底层方法） |
| `reset()` | 重置 `typing_active` 和 `esc_pressed` 状态 |

---

### `utils/config.py`

**职责**：配置文件读写（`.env` 和 `config.ini`）

**关键类**：`ConfigManager`

---

### `utils/extension_setup.py`

**职责**：浏览器扩展管理、Selenium 启动、单实例锁

**关键类**：`ExtensionSetup`

**关键方法**：

| 方法 | 做什么 |
|-----|-------|
| `launch_with_extension(browser, url)` | 启动浏览器并加载扩展（优先 Selenium，回退简单模式） |
| `launch_with_extension_selenium(browser, url)` | 使用 Selenium WebDriver 启动，自动下载匹配 driver |
| `launch_with_extension_simple(browser, url)` | 命令行简单启动，回退方案 |
| `_acquire_single_instance_lock()` | 绑定端口 48573 防止重复启动 |
| `_release_single_instance_lock()` | 释放单实例锁 |
| `get_chrome_path()` | 查找 Chrome 可执行文件路径（Windows/macOS/Linux） |
| `get_edge_path()` | 查找 Edge 可执行文件路径 |
| `get_chrome_version()` | 获取 Chrome 版本号 |
| `get_edge_version()` | 获取 Edge 版本号 |
| `get_extension_dir()` | 查找扩展目录（包含 manifest.json） |
| `open_chrome_extensions()` | 打开 Chrome 扩展管理页面 |
| `open_edge_extensions()` | 打开 Edge 扩展管理页面 |
| `open_extension_folder()` | 打开扩展文件夹 |

---

## WebSocket 消息协议

### 扩展 → 桌面端

| type | 触发时机 | 关键字段 | 处理位置 |
|------|---------|---------|---------|
| `content_auto_input` | 扩展自动提取题目 | `question_content`, `current_code`, `language` | `assistant.py: handle_content_auto_input()` |
| `manual_question` | 用户手动触发 | 同上 | 同上 |
| `test_results` | 页面测试完成 | `results`, `current_code`, `question_content` | `assistant.py: handle_test_results()` |
| `ready_for_input` | 编辑器已就绪 | `code` | `assistant.py: handle_ready_for_input()` |
| `direct_input_complete` | 扩展端写入完成 | `success` | `assistant.py: handle_direct_input_complete()` |
| `progress_request` | 请求进度 | - | `assistant.py: send_progress_update()` |
| `set_language` | 切换语言 | `language` | `assistant.py: set_language()` |
| `sync_code` | 同步代码到桌面 | `code` | `assistant.py: handle_sync_code()` |
| `simulate_input` | 请求模拟键盘输入 | `code`, `interval`, `special_char`, `wait_time` | `assistant.py: handle_simulate_input()` |
| `cancel_request` | 取消输入 | - | `assistant.py: handle_cancel_input()` |
| `sync_input_config` | 配置同步 | `config` | `assistant.py: handle_sync_input_config()` |

### 桌面端 → 扩展

| type | 触发时机 | 关键字段 |
|------|---------|---------|
| `server_ack` | 开始处理 | `status`, `message` |
| `code_solution` | 代码生成完成 | `code`, `language`, `model_used` |
| `code_revision` | 纠错完成 | `code` |
| `input_complete` | 粘贴完成 | `success`, `method_used` |
| `progress_update` | 进度更新 | `progress`, `stage` |
| `sync_code_ack` | 代码同步确认 | `status` |
| `input_progress` | 输入倒计时进度 | `message` |
| `cancel_input_ack` | 取消输入确认 | - |
| `sync_input_config` | 配置同步广播 | `config` |
| `config_info` | 连接成功时发送 | `model` |
| `error` | 错误 | `code`, `message` |

---

## 修改功能时的文件定位

### 1. 修改 AI 生成代码的 Prompt 规则

**文件**：`core/assistant.py`

- `_get_system_prompt(has_test_failure=False)`: 生成代码时的系统指令，`has_test_failure=True` 时返回纠错专用提示词
- `get_complete_code_solution(question, existing_code, test_failure)`: 代码生成主函数，`test_failure` 非空时为纠错模式

---

### 2. 修改代码清理逻辑（去掉 markdown 块）

**文件**：`core/assistant.py`

- `clean_code_response()`: 从 API 响应提取纯代码
- `_is_complete_code()`: 检查代码完整性

---

### 3. 修改桌面输入Tab的UI布局

**文件**：`gui/tabs/input_tab.py`

- `_build_ui()`: 整体布局（语言选择器、输入内容面板、参数面板、按钮行）

---

### 4. 修改输入测试逻辑

**文件**：`gui/tabs/input_tab.py`（调度）+ `utils/input_simulator.py`（底层实现）

- `InputTab._input_test()`: 启动输入测试
- `InputTab._input_test_thread()`: 后台执行逐行输入
- `InputTab._cancel_input()`: 取消输入
- `InputTab._save_config()`: 保存配置并广播
- `InputSimulator._write_text()`: 底层文本写入
- `InputSimulator._press_key()`: 底层按键

---

### 5. 修改日志面板样式/行为

**文件**：`gui/widgets/log_panel.py`

- `LogPanel.__init__()`: UI构建
- `LogPanel.log_message()`: 日志写入格式

---

### 6. 修改获取题目功能

**文件**：`core/assistant.py`（数据来源）+ `gui/main_window.py`（GUI更新）

- `assistant.handle_content_auto_input()`: 扩展端发来题目时，根据 `sync_question` 标志决定是否调用 `gui.set_question()` 更新GUI
- `assistant.handle_sync_code()`: 扩展端同步代码时调用 `gui.set_code()` 更新GUI
- `assistant.handle_simulate_input()`: 扩展端请求模拟输入时执行输入并发送进度更新
- `assistant.handle_cancel_input()`: 处理取消输入请求
- `assistant.handle_sync_input_config()`: 处理配置同步并广播

---

### 7. 修改颜色/主题

**文件**：`gui/themes.py`

所有颜色常量在此统一定义，其他文件通过 `from gui.themes import *` 导入。

---

### 8. 添加新的独立Tab模块

参照 `gui/tabs/input_tab.py` 的模式：
1. 在 `gui/tabs/` 下创建新文件
2. 定义 `XxxTab(ctk.CTkFrame)` 类，接收 `main_window` 参数
3. 在 `gui/main_window.py` 的 `_build_ui()` 中实例化并 pack

---

## 模块化设计原则

1. **gui/themes.py** — 所有颜色常量的唯一来源
2. **gui/widgets/** — 可复用的UI组件，不包含业务逻辑
3. **gui/tabs/** — 独立的Tab模块，通过 `self.mw` 访问 MainWindow 共享状态
4. **gui/main_window.py** — 薄编排层，只负责创建组件和协调交互
5. **core/** — 核心业务逻辑，通过 `gui.set_question()` / `gui.set_code()` 等方法与GUI交互，不直接访问widget
6. **sys.path 管理** — `path_config.py` 在导入时将 `PROJECT_ROOT` 插入 `sys.path` 首位，确保模块可正确导入
