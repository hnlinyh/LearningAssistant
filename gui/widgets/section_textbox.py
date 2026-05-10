import customtkinter as ctk
import threading
from gui.themes import *


class SectionTextbox(ctk.CTkFrame):
    """带标签的文本框组件，支持只读/编辑模式，样式统一。"""

    def __init__(self, master, label_text="内容", height=100, read_only=False, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)

        ctk.CTkLabel(self, text=label_text, text_color=TEXT_PRIMARY, font=("", 13, "bold")).pack(anchor='w', padx=16, pady=(8, 4))
        self.textbox = ctk.CTkTextbox(self, height=height, fg_color=BG, corner_radius=10,
                                      border_width=1, border_color=BORDER,
                                      font=("JetBrains Mono", 12), text_color=TEXT_PRIMARY)
        self.textbox.pack(fill='x', padx=16, pady=(0, 8))

        self._read_only = read_only
        if read_only:
            self.textbox.configure(state="disabled")

    def set_content(self, text: str):
        """替换全部内容（线程安全）。"""
        def _update():
            state = self.textbox.cget("state")
            self.textbox.configure(state="normal")
            self.textbox.delete('1.0', 'end')
            self.textbox.insert('1.0', text)
            if self._read_only:
                self.textbox.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.after(0, _update)

    def get_content(self) -> str:
        """返回当前内容。"""
        return self.textbox.get('1.0', 'end').strip()

    def clear(self):
        """清空内容。"""
        state = self.textbox.cget("state")
        self.textbox.configure(state="normal")
        self.textbox.delete('1.0', 'end')
        if self._read_only:
            self.textbox.configure(state="disabled")

    def set_read_only(self, read_only: bool):
        """切换只读状态。"""
        self._read_only = read_only
        self.textbox.configure(state="disabled" if read_only else "normal")
