import customtkinter as ctk
import threading
import time
from datetime import datetime
from gui.themes import *


class AdvancedInputTestDialog(ctk.CTkToplevel):
    def __init__(self, parent, input_simulator):
        super().__init__(parent)
        self.title("输入测试")
        self.geometry("800x600")
        self.configure(fg_color=BG)
        self.input_simulator = input_simulator
        self.testing = False
        self.test_thread = None

        self._build_ui()

    def _build_ui(self):
        # 标签页
        self.tabview = ctk.CTkTabview(self, fg_color=SURFACE, corner_radius=12,
                                       border_width=1, border_color=BORDER)
        self.tabview.pack(fill='both', expand=True, padx=16, pady=16)

        self.tab_settings = self.tabview.add("输入设置")
        self.tab_log = self.tabview.add("日志信息")

        self._build_settings_tab()
        self._build_log_tab()

    def _build_settings_tab(self):
        frame = self.tab_settings

        # 大文本框
        ctk.CTkLabel(frame, text="输入内容", font=("", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='w', padx=16, pady=(16, 4))
        self.input_text = ctk.CTkTextbox(frame, fg_color=BG, corner_radius=10, height=200,
                                          border_width=1, border_color=BORDER,
                                          font=("JetBrains Mono", 12))
        self.input_text.pack(fill='x', padx=16, pady=(0, 12))
        self.input_text.insert('1.0', 'print("Hello, World!")')

        # 参数设置框
        params_frame = ctk.CTkFrame(frame, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER)
        params_frame.pack(fill='x', padx=16, pady=(0, 12))

        ctk.CTkLabel(params_frame, text="参数设置", font=("", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor='w', padx=12, pady=(8, 4))

        # 等待时间
        row1 = ctk.CTkFrame(params_frame, fg_color='transparent')
        row1.pack(fill='x', padx=12, pady=4)
        ctk.CTkLabel(row1, text="等待时间（秒）:", text_color=TEXT_PRIMARY, width=120).pack(side='left')
        self.wait_time_var = ctk.StringVar(value="2")
        ctk.CTkEntry(row1, textvariable=self.wait_time_var, width=80, fg_color=SURFACE,
                      border_color=BORDER, corner_radius=8).pack(side='left', padx=(4, 0))

        # 输入间隔
        row2 = ctk.CTkFrame(params_frame, fg_color='transparent')
        row2.pack(fill='x', padx=12, pady=4)
        ctk.CTkLabel(row2, text="输入间隔（秒）:", text_color=TEXT_PRIMARY, width=120).pack(side='left')
        self.interval_var = ctk.StringVar(value="0.05")
        ctk.CTkEntry(row2, textvariable=self.interval_var, width=80, fg_color=SURFACE,
                      border_color=BORDER, corner_radius=8).pack(side='left', padx=(4, 0))

        # 特殊字符处理
        row3 = ctk.CTkFrame(params_frame, fg_color='transparent')
        row3.pack(fill='x', padx=12, pady=(4, 12))
        self.special_char_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row3, text="特殊字符处理（转义换行、制表符等）",
                        variable=self.special_char_var, fg_color=PRIMARY,
                        hover_color=PRIMARY_DARK, font=("", 12)).pack(side='left')

        # 按钮
        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=8)

        self.btn_start = ctk.CTkButton(btn_frame, text="开始测试", fg_color=PRIMARY,
                                        hover_color=PRIMARY_DARK, corner_radius=10,
                                        command=self._start_test)
        self.btn_start.pack(side='left', padx=(0, 8))

        self.btn_stop = ctk.CTkButton(btn_frame, text="停止测试", fg_color=ERROR,
                                       hover_color='#dc2626', corner_radius=10,
                                       command=self._stop_test, state="disabled")
        self.btn_stop.pack(side='left', padx=(0, 8))

        ctk.CTkButton(btn_frame, text="清除内容", fg_color='transparent', border_width=1,
                       border_color=BORDER, corner_radius=10, text_color=TEXT_PRIMARY,
                       command=self._clear_content).pack(side='left')

        # 状态
        self.status_label = ctk.CTkLabel(frame, text="准备就绪", text_color=TEXT_SECONDARY, font=("", 12))
        self.status_label.pack(anchor='w', padx=16, pady=(8, 0))

    def _build_log_tab(self):
        frame = self.tab_log

        # 日志区
        header = ctk.CTkFrame(frame, fg_color='transparent')
        header.pack(fill='x', padx=16, pady=(16, 4))
        ctk.CTkLabel(header, text="日志信息", font=("", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(side='left')
        ctk.CTkButton(header, text="清空日志", fg_color='transparent', border_width=1,
                       border_color=BORDER, corner_radius=8, text_color=TEXT_SECONDARY,
                       width=70, height=28, font=("", 11),
                       command=self._clear_log).pack(side='right')

        self.log_text = ctk.CTkTextbox(frame, fg_color=BG, corner_radius=10, border_width=1,
                                        border_color=BORDER, font=("JetBrains Mono", 11),
                                        text_color=TEXT_PRIMARY, state="disabled")
        self.log_text.pack(fill='both', expand=True, padx=16, pady=(0, 16))

    def _log(self, msg):
        time_str = datetime.now().strftime('%H:%M:%S')
        def _update():
            self.log_text.configure(state="normal")
            self.log_text.insert('end', f"[{time_str}] {msg}\n")
            self.log_text.see('end')
            self.log_text.configure(state="disabled")
        self.after(0, _update)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state="disabled")

    def _clear_content(self):
        self.input_text.delete('1.0', 'end')

    def _start_test(self):
        text = self.input_text.get('1.0', 'end').strip()
        if not text:
            self.status_label.configure(text="请输入测试内容")
            return

        try:
            wait_time = float(self.wait_time_var.get())
            interval = float(self.interval_var.get())
        except ValueError:
            self.status_label.configure(text="参数格式错误，请输入数字")
            return

        self.testing = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.test_thread = threading.Thread(target=self._test_thread,
                                             args=(text, wait_time, interval),
                                             daemon=True)
        self.test_thread.start()

    def _test_thread(self, text, wait_time, interval):
        self._log("测试开始")
        self.after(0, lambda: self.status_label.configure(text="倒计时中..."))

        # 倒计时
        for i in range(int(wait_time), 0, -1):
            if not self.testing:
                self._log("测试已取消")
                self.after(0, self._reset)
                return
            self.after(0, lambda n=i: self.status_label.configure(text=f"倒计时: {n}..."))
            self._log(f"倒计时: {i}")
            time.sleep(1)

        self._log("开始输入")
        self.after(0, lambda: self.status_label.configure(text="输入中..."))

        # 处理特殊字符
        if self.special_char_var.get():
            text = text.replace('\\n', '\n').replace('\\t', '\t')

        # 逐行输入
        lines = text.split('\n')
        total = len(lines)
        for i, line in enumerate(lines):
            if not self.testing:
                self._log("输入已中断")
                break
            self.input_simulator._write_text(line)
            if i < total - 1:
                self.input_simulator._press_key('enter')
            progress = int((i + 1) / total * 100)
            self.after(0, lambda p=progress: self.status_label.configure(text=f"输入中... {p}%"))
            self._log(f"已输入第 {i + 1}/{total} 行")
            time.sleep(interval)

        self._log("测试完成")
        self.after(0, self._reset)

    def _stop_test(self):
        self.testing = False
        self._log("正在停止...")

    def _reset(self):
        self.testing = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text="准备就绪")
