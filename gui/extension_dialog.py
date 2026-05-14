import customtkinter as ctk
import threading
from gui.themes import *


class ExtensionInstallDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("安装浏览器扩展")
        self.geometry("620x750")
        self.configure(fg_color=BG)
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        scroll.pack(fill='both', expand=True, padx=24, pady=16)

        # Header: rocket icon + title + description
        header = ctk.CTkFrame(scroll, fg_color='transparent')
        header.pack(fill='x', pady=(0, 16))
        ctk.CTkLabel(header, text="🚀", font=("", 36)).pack(anchor='center')
        ctk.CTkLabel(header, text="安装浏览器扩展", font=("", 22, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='center', pady=(8, 4))
        ctk.CTkLabel(header, text="浏览器扩展是学习助手的核心组件，用于自动提取题目、写入代码",
                     text_color=TEXT_SECONDARY, font=("", 12), wraplength=500).pack(anchor='center')

        # Why install
        self._add_section(scroll, "为什么需要安装浏览器扩展？",
                          "浏览器扩展负责在编程学习平台（如头歌 Educoder、力扣 LeetCode、牛客等）上自动提取题目内容、"
                          "读取编辑器代码、以及将 AI 生成的代码写入编辑器。没有扩展，桌面端无法与网页交互。")

        # Manual install section
        manual_frame = ctk.CTkFrame(scroll, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        manual_frame.pack(fill='x', pady=(0, 12))
        ctk.CTkLabel(manual_frame, text="手动安装", font=("", 14, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(12, 4))
        ctk.CTkLabel(manual_frame, text="打开扩展管理页面，手动加载已解压的扩展程序",
                     text_color=TEXT_SECONDARY, font=("", 12), wraplength=520).pack(anchor='w', padx=16, pady=(0, 8))

        manual_btn_frame = ctk.CTkFrame(manual_frame, fg_color='transparent')
        manual_btn_frame.pack(fill='x', padx=16, pady=(0, 8))
        ctk.CTkButton(manual_btn_frame, text="打开 Chrome 扩展管理", fg_color=SURFACE, border_width=1,
                       border_color=BORDER, corner_radius=8, height=34, text_color=TEXT_PRIMARY,
                       font=("", 12), hover_color=PRIMARY_LIGHT,
                       command=lambda: self._run_async(self._open_chrome_ext)).pack(side='left', expand=True, fill='x', padx=(0, 4))
        ctk.CTkButton(manual_btn_frame, text="打开 Edge 扩展管理", fg_color=SURFACE, border_width=1,
                       border_color=BORDER, corner_radius=8, height=34, text_color=TEXT_PRIMARY,
                       font=("", 12), hover_color=PRIMARY_LIGHT,
                       command=lambda: self._run_async(self._open_edge_ext)).pack(side='left', expand=True, fill='x', padx=(4, 0))

        ctk.CTkButton(manual_frame, text="打开扩展文件夹", fg_color=SURFACE, border_width=1,
                       border_color=BORDER, corner_radius=8, height=34, text_color=TEXT_PRIMARY,
                       font=("", 12), hover_color=PRIMARY_LIGHT,
                       command=lambda: self._run_async(self._open_ext_folder)).pack(fill='x', padx=16, pady=(0, 8))

        self.manual_status_label = ctk.CTkLabel(manual_frame, text="", text_color=TEXT_SECONDARY, font=("", 11))
        self.manual_status_label.pack(anchor='w', padx=16, pady=(0, 12))

        # Launch browser section
        launch_frame = ctk.CTkFrame(scroll, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        launch_frame.pack(fill='x', pady=(0, 12))
        ctk.CTkLabel(launch_frame, text="启动浏览器", font=("", 14, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(12, 4))
        ctk.CTkLabel(launch_frame, text="Chrome 会启动 Chrome for Testing（开发专用），Edge 使用本机浏览器自动加载扩展",
                     text_color=TEXT_SECONDARY, font=("", 12), wraplength=520).pack(anchor='w', padx=16, pady=(0, 8))

        launch_btn_frame = ctk.CTkFrame(launch_frame, fg_color='transparent')
        launch_btn_frame.pack(fill='x', padx=16, pady=(0, 8))
        ctk.CTkButton(launch_btn_frame, text="启动 Chrome for Testing", fg_color=SUCCESS, hover_color='#0D9668',
                       corner_radius=8, height=34, font=("", 12, "bold"),
                       command=lambda: self._run_async(lambda: self._launch_browser('chrome'))).pack(side='left', expand=True, fill='x', padx=(0, 4))
        ctk.CTkButton(launch_btn_frame, text="启动 Edge", fg_color=SUCCESS, hover_color='#0D9668',
                       corner_radius=8, height=34, font=("", 12, "bold"),
                       command=lambda: self._run_async(lambda: self._launch_browser('edge'))).pack(side='left', expand=True, fill='x', padx=(4, 0))

        self.launch_status_label = ctk.CTkLabel(launch_frame, text="", text_color=TEXT_SECONDARY, font=("", 11))
        self.launch_status_label.pack(anchor='w', padx=16, pady=(0, 12))

        # Bottom: dismiss button
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=24, pady=(0, 16))
        ctk.CTkButton(btn_frame, text="稍后安装", fg_color='transparent', border_width=1,
                       border_color=BORDER, corner_radius=10, height=36,
                       text_color=TEXT_PRIMARY, font=("", 12),
                       command=self.destroy).pack(fill='x')

    def _add_section(self, parent, title, content):
        frame = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        frame.pack(fill='x', pady=(0, 12))
        ctk.CTkLabel(frame, text=title, font=("", 14, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(12, 4))
        ctk.CTkLabel(frame, text=content, text_color=TEXT_SECONDARY, font=("", 12),
                     wraplength=520, justify='left').pack(anchor='w', padx=16, pady=(0, 12))

    def _run_async(self, func):
        """Run a function in a background thread."""
        threading.Thread(target=func, daemon=True).start()

    def _open_chrome_ext(self):
        from utils.extension_setup import ExtensionSetup
        es = ExtensionSetup()
        success, msg = es.open_chrome_extensions()
        color = SUCCESS if success else '#EF4444'
        self.after(0, lambda: self.manual_status_label.configure(text=msg, text_color=color))

    def _open_edge_ext(self):
        from utils.extension_setup import ExtensionSetup
        es = ExtensionSetup()
        success, msg = es.open_edge_extensions()
        color = SUCCESS if success else '#EF4444'
        self.after(0, lambda: self.manual_status_label.configure(text=msg, text_color=color))

    def _open_ext_folder(self):
        from utils.extension_setup import ExtensionSetup
        es = ExtensionSetup()
        success, msg = es.open_extension_folder()
        color = SUCCESS if success else '#EF4444'
        self.after(0, lambda: self.manual_status_label.configure(text=msg, text_color=color))

    def _launch_browser(self, browser):
        from utils.extension_setup import ExtensionSetup
        es = ExtensionSetup()
        self.after(0, lambda: self.launch_status_label.configure(text="正在准备启动浏览器...", text_color=TEXT_SECONDARY))
        success, msg = es.launch_with_extension(
            browser=browser,
            progress_callback=lambda progress: self.after(
                0,
                lambda: self.launch_status_label.configure(text=progress, text_color=TEXT_SECONDARY),
            ),
        )
        color = SUCCESS if success else '#EF4444'
        self.after(0, lambda: self.launch_status_label.configure(text=msg, text_color=color))
