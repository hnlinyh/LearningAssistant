import customtkinter as ctk
import json
import tkinter as tk
import threading
import os
import sys
from gui.themes import *

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("学习助手 v1.0")
        self.geometry("900x640")
        self.minsize(900, 640)
        self.configure(fg_color=BG)

        # State
        self.server_running = False
        self.server_manager = None
        self.selected_model = ctk.StringVar(value='')
        self.selected_language = ctk.StringVar(value='Python')
        self.model_list = []

        # Managers (lazy init)
        self._config_manager = None
        self._model_manager = None
        self._input_simulator = None
        self._extension_setup = None

        self._build_ui()
        self._load_config_from_env()
        # 模型选择变更时自动保存
        self.selected_model.trace_add('write', lambda *_: self._save_config_to_env())
        self._setup_tray()

    @property
    def config_manager(self):
        if self._config_manager is None:
            from utils.config import ConfigManager
            self._config_manager = ConfigManager()
        return self._config_manager

    @property
    def model_manager(self):
        if self._model_manager is None:
            from gui.model_manager import ModelManager
            self._model_manager = ModelManager(self)
        return self._model_manager

    @property
    def input_simulator(self):
        if self._input_simulator is None:
            from utils.input_simulator import InputSimulator
            self._input_simulator = InputSimulator(self)
        return self._input_simulator

    @property
    def extension_setup(self):
        if self._extension_setup is None:
            from utils.extension_setup import ExtensionSetup
            self._extension_setup = ExtensionSetup()
        return self._extension_setup

    def _build_ui(self):
        # Header
        self.header = tk.Canvas(self, height=64, highlightthickness=0)
        self.header.pack(fill='x')
        self.header.bind('<Configure>', self._draw_header)

        # Tab view — 不再expand，固定在顶部
        self.tabview = ctk.CTkTabview(self, fg_color=SURFACE, corner_radius=12,
                                       border_width=1, border_color=BORDER)
        self.tabview.pack(fill='x', padx=16, pady=(0, 8))

        # Create tabs
        self.tab_model = self.tabview.add("AI 模型")
        self.tab_input = self.tabview.add("桌面输入")
        self.tab_config = self.tabview.add("运行配置")
        self.tab_server = self.tabview.add("服务器")

        self._build_model_tab()
        # 桌面输入Tab — 使用独立的InputTab组件
        from gui.tabs.input_tab import InputTab
        self.input_tab = InputTab(self.tab_input, main_window=self)
        self.input_tab.pack(fill='both', expand=True)
        self._build_config_tab()
        self._build_server_tab()

        # 日志区 — 使用LogPanel组件，占满剩余空间
        from gui.widgets.log_panel import LogPanel
        self.log_panel = LogPanel(self)
        self.log_panel.pack(fill='both', expand=True, padx=16, pady=(0, 8))

        # Footer links
        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', padx=16, pady=(0, 8))
        for text in ["帮助", "使用条款", "开源许可", "官网"]:
            ctk.CTkLabel(footer, text=text, text_color=PRIMARY, cursor="hand2", font=("", 11)).pack(side='left', padx=8)

    def _draw_header(self, event=None):
        self.header.delete('all')
        w = self.header.winfo_width()
        # Gradient
        steps = 100
        for i in range(steps):
            r1, g1, b1 = 0x4F, 0x6B, 0xED
            r2, g2, b2 = 0x7C, 0x3A, 0xED
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            x1 = w * i / steps
            x2 = w * (i + 1) / steps
            self.header.create_rectangle(x1, 0, x2, 64, fill=f'#{r:02x}{g:02x}{b:02x}', outline='')
        self.header.create_text(24, 20, text='◉ 学习助手 v1.0', fill='white', font=('', 16, 'bold'), anchor='w')
        self.header.create_text(24, 44, text='欢迎使用', fill='#E0E0E0', font=('', 11), anchor='w')

    def _build_model_tab(self):
        frame = self.tab_model
        # API URL
        ctk.CTkLabel(frame, text="API 基础 URL", text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(16, 4))
        self.api_url_entry = ctk.CTkEntry(frame, fg_color=SURFACE, border_color=BORDER, corner_radius=8,
                                           placeholder_text="https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.api_url_entry.pack(fill='x', padx=16, pady=(0, 8))
        self.api_url_entry.insert(0, os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'))

        # API Key
        ctk.CTkLabel(frame, text="API Key", text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(0, 4))
        self.api_key_entry = ctk.CTkEntry(frame, fg_color=SURFACE, border_color=BORDER, corner_radius=8,
                                           show='*', placeholder_text="输入 API Key")
        self.api_key_entry.pack(fill='x', padx=16, pady=(0, 8))
        self.api_key_entry.insert(0, os.getenv('OPENAI_API_KEY', ''))

        # Buttons row
        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=4)
        ctk.CTkButton(btn_frame, text="获取模型", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                       corner_radius=10, command=self._fetch_models).pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_frame, text="测试选中模型", fg_color=SUCCESS, hover_color='#0d9668',
                       corner_radius=10, command=self._test_model).pack(side='left')

        # Filter
        self.model_filter = ctk.CTkEntry(frame, fg_color=SURFACE, border_color=BORDER, corner_radius=8,
                                          placeholder_text="输入关键词筛选模型...")
        self.model_filter.pack(fill='x', padx=16, pady=8)
        self.model_filter.bind('<KeyRelease>', self._filter_models)

        # 选中模型时清空筛选框并显示选中的模型
        self.selected_model.trace_add('write', self._on_model_selected)

        # Model list
        self.model_list_frame = ctk.CTkScrollableFrame(frame, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER)
        self.model_list_frame.pack(fill='both', expand=True, padx=16, pady=(0, 16))

    def _build_config_tab(self):
        frame = self.tab_config
        self.config_frame_inner = ctk.CTkFrame(frame, fg_color='transparent')
        self.config_frame_inner.pack(fill='both', expand=True, padx=16, pady=16)

        self.config_paste_mode = ctk.BooleanVar(value=True)
        self.config_show_log = ctk.BooleanVar(value=True)
        self.config_auto_start = ctk.BooleanVar(value=False)
        self.config_minimize_tray = ctk.BooleanVar(value=True)

        for text, var in [
            ("启用复制粘贴模式", self.config_paste_mode),
            ("显示日志", self.config_show_log),
            ("开机自启", self.config_auto_start),
            ("关闭时最小化到托盘", self.config_minimize_tray),
        ]:
            ctk.CTkSwitch(self.config_frame_inner, text=text, variable=var,
                          progress_color=PRIMARY, font=("", 13)).pack(anchor='w', pady=8)

        # 安装浏览器扩展按钮
        ctk.CTkButton(self.config_frame_inner, text="安装浏览器扩展", fg_color=PRIMARY,
                       hover_color=PRIMARY_DARK, corner_radius=10, height=36,
                       font=("", 13), command=self._show_extension_dialog).pack(anchor='w', pady=(16, 0))

    def _build_server_tab(self):
        frame = self.tab_server

        # 端口配置行
        port_frame = ctk.CTkFrame(frame, fg_color='transparent')
        port_frame.pack(fill='x', padx=16, pady=(16, 4))
        ctk.CTkLabel(port_frame, text="端口:", text_color=TEXT_PRIMARY, font=("", 13)).pack(side='left')
        ctk.CTkButton(port_frame, text="−", width=32, height=28, fg_color=SURFACE, hover_color=PRIMARY_LIGHT,
                       text_color=TEXT_PRIMARY, border_color=BORDER, border_width=1, corner_radius=6,
                       font=("", 14), command=lambda: self._adjust_port(-1)).pack(side='left', padx=(8, 2))
        self.ws_port_entry = ctk.CTkEntry(port_frame, width=80, height=28, fg_color=SURFACE, border_color=BORDER,
                                           corner_radius=6, font=("", 13), justify='center')
        self.ws_port_entry.pack(side='left', padx=2)
        self.ws_port_entry.insert(0, os.getenv('WS_PORT', '8000'))
        ctk.CTkButton(port_frame, text="+", width=32, height=28, fg_color=SURFACE, hover_color=PRIMARY_LIGHT,
                       text_color=TEXT_PRIMARY, border_color=BORDER, border_width=1, corner_radius=6,
                       font=("", 14), command=lambda: self._adjust_port(1)).pack(side='left', padx=(2, 0))

        self.server_status_frame = ctk.CTkFrame(frame, fg_color='transparent')
        self.server_status_frame.pack(fill='x', padx=16, pady=8)

        self.server_indicator = tk.Canvas(self.server_status_frame, width=12, height=12, highlightthickness=0)
        self.server_indicator.pack(side='left', padx=(0, 8))
        self.server_indicator.create_oval(2, 2, 10, 10, fill=ERROR, outline='')

        self.server_label = ctk.CTkLabel(self.server_status_frame, text="服务器未运行", text_color=TEXT_PRIMARY, font=("", 14))
        self.server_label.pack(side='left')

        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=8)
        self.btn_start_server = ctk.CTkButton(btn_frame, text="启动服务器", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                                               corner_radius=10, command=self._start_server)
        self.btn_start_server.pack(side='left', padx=(0, 8))
        self.btn_stop_server = ctk.CTkButton(btn_frame, text="停止服务器", fg_color=ERROR, hover_color='#dc2626',
                                              corner_radius=10, command=self._stop_server, state="disabled")
        self.btn_stop_server.pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_frame, text="启动浏览器", fg_color=SUCCESS, hover_color='#0d9668',
                       corner_radius=10, command=self._launch_browser).pack(side='left')

    def _adjust_port(self, delta):
        try:
            port = int(self.ws_port_entry.get().strip()) + delta
            port = max(1024, min(65535, port))
            self.ws_port_entry.delete(0, 'end')
            self.ws_port_entry.insert(0, str(port))
        except ValueError:
            self.ws_port_entry.delete(0, 'end')
            self.ws_port_entry.insert(0, '8000')

    # ========== Actions ==========
    def _fetch_models(self):
        api_key = self.api_key_entry.get().strip()
        base_url = self.api_url_entry.get().strip()
        if not api_key:
            self.log_message("请先输入 API Key")
            return
        self._save_config_to_env()
        self.log_message("正在获取模型列表...")
        threading.Thread(target=self._fetch_models_thread, args=(api_key, base_url), daemon=True).start()

    def _fetch_models_thread(self, api_key, base_url):
        import asyncio
        models = asyncio.run(self.model_manager.fetch_models(api_key, base_url))
        self.after(0, self._update_model_list, models)

    def _update_model_list(self, models):
        self.model_list = models
        for w in self.model_list_frame.winfo_children():
            w.destroy()
        # 保留已选中的模型
        current_model = self.selected_model.get()
        if current_model and current_model not in models:
            models = models + [current_model]
        for model in models:
            rb = ctk.CTkRadioButton(self.model_list_frame, text=model, variable=self.selected_model, value=model,
                                     fg_color=PRIMARY, hover_color=PRIMARY_DARK, font=("", 12))
            rb.pack(anchor='w', padx=8, pady=2)
        self.log_message(f"获取到 {len(models)} 个模型")
        self._save_config_to_env()

    def _filter_models(self, event=None):
        keyword = self.model_filter.get().strip().lower()
        for w in self.model_list_frame.winfo_children():
            if isinstance(w, ctk.CTkRadioButton):
                w.destroy()
        filtered = [m for m in self.model_list if keyword in m.lower()] if keyword else self.model_list
        for model in filtered:
            rb = ctk.CTkRadioButton(self.model_list_frame, text=model, variable=self.selected_model, value=model,
                                     fg_color=PRIMARY, hover_color=PRIMARY_DARK, font=("", 12))
            rb.pack(anchor='w', padx=8, pady=2)

    def _on_model_selected(self, *args):
        """选中模型时清空筛选框并保存配置。"""
        model = self.selected_model.get()
        if model:
            self.model_filter.delete(0, 'end')
            self.model_filter.insert(0, model)
            self._save_config_to_env()

    def _test_model(self):
        model = self.selected_model.get()
        if not model:
            self.log_message("请先选择一个模型")
            return
        api_key = self.api_key_entry.get().strip()
        base_url = self.api_url_entry.get().strip()
        self.log_message(f"正在测试模型: {model}...")
        threading.Thread(target=self._test_model_thread, args=(api_key, base_url, model), daemon=True).start()

    def _test_model_thread(self, api_key, base_url, model):
        import asyncio
        result = asyncio.run(self.model_manager.test_model(api_key, base_url, model))
        self.after(0, self._show_test_result, model, result)

    def _show_test_result(self, model, result):
        if result.get('success'):
            latency = result.get('latency', 0)
            self.log_message(f"✅ {model} 响应正常 ({latency:.1f}s)")
        else:
            self.log_message(f"❌ {model} 测试失败: {result.get('error', '未知错误')}")

    def _start_server(self):
        if self.server_running:
            return
        self._save_config_to_env()

        # 读取端口
        port_str = self.ws_port_entry.get().strip()
        try:
            ws_port = int(port_str) if port_str else int(os.getenv('WS_PORT', '8000'))
            if not (1024 <= ws_port <= 65535):
                self.log_message("端口号范围: 1024-65535")
                return
        except ValueError:
            self.log_message("端口号格式错误，请输入数字")
            return

        # 构建完整的模型配置，包含 API 配置
        model_info = {}
        if self.selected_model.get():
            model_info['model'] = self.selected_model.get()
        api_key = self.api_key_entry.get().strip()
        base_url = self.api_url_entry.get().strip()
        if api_key:
            model_info['api_key'] = api_key
        if base_url:
            model_info['base_url'] = base_url

        from core.server import ServerManager
        self.server_manager = ServerManager(self, model_info, port=ws_port)
        self.server_manager.start()
        self.server_running = True
        self.btn_start_server.configure(state="disabled")
        self.btn_stop_server.configure(state="normal")
        self.server_indicator.delete('all')
        self.server_indicator.create_oval(2, 2, 10, 10, fill=SUCCESS, outline='')
        host = os.getenv('WS_HOST', 'localhost')

        # 写入端口配置到扩展目录，供扩展端自动读取
        try:
            from path_config import CHROME_EXTENSION_PATH
            config_path = os.path.join(CHROME_EXTENSION_PATH, 'server-config.json')
            ocr_api_url = 'https://ocr.yhsun.cn/'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "ws_port": ws_port,
                    "ws_url": f"ws://{host}:{ws_port}",
                    "ocr_api_url": ocr_api_url
                }, f)
        except Exception as e:
            self.log_message(f"写入扩展配置失败: {e}")
        self.server_label.configure(text=f"服务器运行中  {host}:{ws_port}")

    def _stop_server(self):
        if not self.server_running:
            return
        if self.server_manager:
            self.server_manager.stop()
        self.server_running = False
        self.btn_start_server.configure(state="normal")
        self.btn_stop_server.configure(state="disabled")
        self.server_indicator.delete('all')
        self.server_indicator.create_oval(2, 2, 10, 10, fill=ERROR, outline='')
        self.server_label.configure(text="服务器未运行")

    def _launch_browser(self):
        if not self.server_running:
            self.log_message("请先启动服务器")
            return
        success, msg = self.extension_setup.launch_with_extension()
        self.log_message(msg)

    def _setup_tray(self):
        try:
            import pystray
            from PIL import Image
            # Create a simple icon
            icon_image = Image.new('RGB', (64, 64), color=PRIMARY)

            def on_show(icon, item):
                icon.stop()
                self.after(0, self.deiconify)

            def on_quit(icon, item):
                icon.stop()
                self.after(0, self.destroy)

            menu = pystray.Menu(
                pystray.MenuItem('显示', on_show, default=True),
                pystray.MenuItem('退出', on_quit)
            )
            self.tray_icon = pystray.Icon('learning_assistant', icon_image, '学习助手', menu)

            self.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            self.tray_icon = None

    def _on_close(self):
        if self.config_minimize_tray.get() and self.tray_icon:
            self.withdraw()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        else:
            if self.server_running:
                self._stop_server()
            self.destroy()

    def log_message(self, msg):
        """委托给LogPanel组件（保持向后兼容）。"""
        self.log_panel.log_message(msg)

    def set_question(self, question: str):
        """供assistant.py调用，更新输入内容框（线程安全）。"""
        if hasattr(self, 'input_tab'):
            self.after(0, self._do_set_input_content, question)

    def set_code(self, code: str):
        """供assistant.py调用，更新输入内容框（线程安全）。"""
        if hasattr(self, 'input_tab'):
            self.after(0, self._do_set_input_content, code)

    def _do_set_input_content(self, text: str):
        self.input_tab.input_content_text.delete('1.0', 'end')
        self.input_tab.input_content_text.insert('1.0', text)

    def _show_extension_dialog(self):
        from gui.extension_dialog import ExtensionInstallDialog
        ExtensionInstallDialog(self)

    # ========== .env 配置持久化 ==========

    def _save_config_to_env(self):
        """从 GUI 控件读取当前配置并保存到 .env 文件。只保存非空值。"""
        data = {}
        api_key = self.api_key_entry.get().strip()
        base_url = self.api_url_entry.get().strip()
        model = self.selected_model.get()

        if api_key:
            data['OPENAI_API_KEY'] = api_key
        if base_url:
            data['OPENAI_BASE_URL'] = base_url
        if model:
            data['OPENAI_MODEL'] = model

        # 保存端口
        port_str = self.ws_port_entry.get().strip()
        if port_str:
            data['WS_PORT'] = port_str

        # 只有有数据需要保存时才调用 save_to_env
        if data:
            self.config_manager.save_to_env(data)

    def _load_config_from_env(self):
        """从 .env 文件加载配置并填充到 GUI 控件。"""
        data = self.config_manager.load_from_env()
        if not data:
            return

        api_key = data.get('OPENAI_API_KEY', '')
        base_url = data.get('OPENAI_BASE_URL', '')
        model = data.get('OPENAI_MODEL', '')
        ws_port = data.get('WS_PORT', '')

        if api_key:
            self.api_key_entry.delete(0, 'end')
            self.api_key_entry.insert(0, api_key)
        if base_url:
            self.api_url_entry.delete(0, 'end')
            self.api_url_entry.insert(0, base_url)
        if model:
            self.selected_model.set(model)
            self.model_list.append(model)
            rb = ctk.CTkRadioButton(self.model_list_frame, text=model, variable=self.selected_model, value=model,
                                     fg_color=PRIMARY, hover_color=PRIMARY_DARK, font=("", 12))
            rb.pack(anchor='w', padx=8, pady=2)
        if ws_port:
            self.ws_port_entry.delete(0, 'end')
            self.ws_port_entry.insert(0, ws_port)
