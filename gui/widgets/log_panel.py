import customtkinter as ctk
import threading
from datetime import datetime
from gui.themes import *


class LogPanel(ctk.CTkFrame):
    """可复用的日志显示面板，支持线程安全写入。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER, **kwargs)

        ctk.CTkLabel(self, text="日志", font=("", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor='w', padx=12, pady=(8, 0))
        self.log_text = ctk.CTkTextbox(self, fg_color=BG, corner_radius=10,
                                       font=("JetBrains Mono", 11), text_color=TEXT_PRIMARY, state="disabled")
        self.log_text.pack(fill='both', expand=True, padx=12, pady=8)

    def log_message(self, msg: str):
        """线程安全的日志写入，自动添加时间戳。"""
        time_str = datetime.now().strftime('%H:%M:%S')

        def _update():
            self.log_text.configure(state="normal")
            self.log_text.insert('end', f"{time_str}  {msg}\n")
            self.log_text.see('end')
            self.log_text.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.after(0, _update)

    def clear(self):
        """清空日志内容。"""
        self.log_text.configure(state="normal")
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state="disabled")
