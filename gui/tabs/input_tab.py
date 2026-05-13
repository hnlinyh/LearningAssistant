import customtkinter as ctk
import threading
import time
from gui.themes import *


class InputTab(ctk.CTkFrame):
    """桌面输入Tab — 代码生成、复制、粘贴、输入测试。

    Args:
        master: 父容器（tabview的tab frame）
        main_window: MainWindow引用，用于访问共享状态
    """

    def __init__(self, master, main_window):
        super().__init__(master, fg_color='transparent')
        self.mw = main_window
        self._build_ui()

    def _build_ui(self):
        # ── 语言选择器 ──
        lang_frame = ctk.CTkFrame(self, fg_color='transparent')
        lang_frame.pack(fill='x', padx=16, pady=(16, 4))
        ctk.CTkLabel(lang_frame, text="编程语言:", text_color=TEXT_PRIMARY).pack(side='left')
        self.lang_menu = ctk.CTkOptionMenu(
            lang_frame, values=["Python", "JavaScript", "Java", "C++", "C", "C#"],
            fg_color=SURFACE, button_color=PRIMARY, button_hover_color=PRIMARY_DARK,
            dropdown_fg_color=SURFACE, dropdown_hover_color=PRIMARY_LIGHT,
            variable=self.mw.selected_language)
        self.lang_menu.pack(side='left', padx=8)

        # ── 输入内容面板（可编辑） ──
        ctk.CTkLabel(self, text="输入内容", text_color=TEXT_PRIMARY, font=("", 13, "bold")).pack(anchor='w', padx=16, pady=(8, 4))
        self.input_content_text = ctk.CTkTextbox(self, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER,
                                                  font=("JetBrains Mono", 12), text_color=TEXT_PRIMARY)
        self.input_content_text.pack(fill='both', expand=True, padx=16, pady=(0, 8))

        # ── 输入测试参数 ──
        params_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER)
        params_frame.pack(fill='x', padx=16, pady=(0, 8))

        row1 = ctk.CTkFrame(params_frame, fg_color='transparent')
        row1.pack(fill='x', padx=12, pady=(8, 2))
        ctk.CTkLabel(row1, text="等待时间（秒）:", text_color=TEXT_PRIMARY).pack(side='left')
        self.input_wait_time_var = ctk.StringVar(value="2")
        ctk.CTkEntry(row1, textvariable=self.input_wait_time_var, width=80, fg_color=SURFACE,
                     border_color=BORDER, corner_radius=8).pack(side='left', padx=(4, 16))
        ctk.CTkLabel(row1, text="输入间隔（秒）:", text_color=TEXT_PRIMARY).pack(side='left')
        self.input_interval_var = ctk.StringVar(value="0.05")
        ctk.CTkEntry(row1, textvariable=self.input_interval_var, width=80, fg_color=SURFACE,
                     border_color=BORDER, corner_radius=8).pack(side='left', padx=(4, 0))

        row2 = ctk.CTkFrame(params_frame, fg_color='transparent')
        row2.pack(fill='x', padx=12, pady=(2, 8))
        self.input_special_char_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row2, text="特殊字符处理（转义换行、制表符等）",
                        variable=self.input_special_char_var, fg_color=PRIMARY,
                        hover_color=PRIMARY_DARK, font=("", 12)).pack(side='left')

        # ── 按钮行 ──
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=(0, 16))
        ctk.CTkButton(btn_frame, text="复制代码", fg_color=SUCCESS, hover_color='#0d9668',
                      corner_radius=10, command=self._copy_code).pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_frame, text="模拟键盘输入", fg_color=TEXT_SECONDARY, hover_color='#475569',
                      corner_radius=10, command=self._input_test).pack(side='left', padx=(0, 8))
        self.cancel_btn = ctk.CTkButton(btn_frame, text="取消输入", fg_color=WARNING, hover_color='#D97706',
                                         corner_radius=10, command=self._cancel_input, state='disabled')
        self.cancel_btn.pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_frame, text="保存配置", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                      corner_radius=10, command=self._save_config).pack(side='left', padx=(0, 8))

    # ========== 复制代码 ==========

    def _copy_code(self):
        code = self.input_content_text.get('1.0', 'end').strip()
        if code and code != "生成失败，请检查 API 配置":
            self.clipboard_clear()
            self.clipboard_append(code)
            self.mw.log_message("代码已复制到剪贴板")
        else:
            self.mw.log_message("没有可复制的代码")

    # ========== 模拟键盘输入 ==========

    def _input_test(self):
        text = self.input_content_text.get('1.0', 'end').strip()
        if not text:
            self.mw.log_message("输入内容面板为空，请先输入或生成代码")
            return
        params = self._validate_test_params()
        if params is None:
            return
        wait_time, interval = params
        self.mw.log_message(f"输入测试将在 {int(wait_time)} 秒后开始，请切换到目标窗口...")
        # 启用取消按钮
        self.cancel_btn.configure(state='normal')
        threading.Thread(target=self._input_test_thread, args=(text, wait_time, interval), daemon=True).start()

    def _input_test_thread(self, text, wait_time, interval):
        for i in range(int(wait_time), 0, -1):
            self.after(0, self.mw.log_message, f"倒计时: {i}...")
            time.sleep(1)

        self.after(0, self.mw.log_message, "开始输入...")

        if self.input_special_char_var.get():
            text = text.replace('\\n', '\n').replace('\\t', '\t')

        self.mw.input_simulator.reset()
        self.mw.input_simulator.typing_active = True
        lines = text.split('\n')
        total = len(lines)
        success = True
        for i, line in enumerate(lines):
            if not self.mw.input_simulator.typing_active:
                self.after(0, self.mw.log_message, "输入已中断")
                success = False
                break
            self.mw.input_simulator._write_text(line)
            if i < total - 1:
                self.mw.input_simulator._press_key('enter')
            progress = int((i + 1) / total * 100)
            self.after(0, self.mw.log_message, f"输入中... {progress}%")
            time.sleep(interval)

        if success:
            self.after(0, self.mw.log_message, "模拟键盘输入完成")
        # 禁用取消按钮
        self.after(0, lambda: self.cancel_btn.configure(state='disabled'))

    # ========== 取消输入 ==========

    def _cancel_input(self):
        self.mw.input_simulator.typing_active = False
        self.mw.log_message("输入已取消")
        self.cancel_btn.configure(state='disabled')

    # ========== 保存配置 ==========

    def _save_config(self):
        params = self._validate_test_params()
        if params is None:
            return
        wait_time, interval = params
        config = {
            "wait_time": wait_time,
            "interval": interval,
            "special_char": self.input_special_char_var.get()
        }
        # 通过server_manager广播配置
        if hasattr(self.mw, 'server_manager') and self.mw.server_manager:
            self.mw.server_manager.broadcast_config(config)
        self.mw.log_message("配置已保存并同步到扩展端")

    # ========== 参数验证 ==========

    def _validate_test_params(self):
        try:
            wait_time = float(self.input_wait_time_var.get())
            interval = float(self.input_interval_var.get())
        except ValueError:
            self.mw.log_message("参数格式错误，请输入数字")
            return None
        if wait_time < 0 or interval < 0:
            self.mw.log_message("参数不能为负数")
            return None
        return wait_time, interval
