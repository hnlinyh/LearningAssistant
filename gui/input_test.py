import customtkinter as ctk
import threading
import time

PRIMARY = '#4F6BED'
PRIMARY_DARK = '#3B52CC'
BG = '#F8FAFC'
TEXT_PRIMARY = '#1E293B'
BORDER = '#E2E8F0'

class InputTestDialog(ctk.CTkToplevel):
    def __init__(self, parent, input_simulator):
        super().__init__(parent)
        self.title("输入测试")
        self.geometry("440x320")
        self.configure(fg_color=BG)
        self.input_simulator = input_simulator
        self.testing = False

        ctk.CTkLabel(self, text="输入测试", font=("", 16, "bold"), text_color=TEXT_PRIMARY).pack(pady=(16, 8))

        self.text_input = ctk.CTkTextbox(self, fg_color='white', corner_radius=10, height=120,
                                          border_width=1, border_color=BORDER)
        self.text_input.pack(fill='x', padx=16, pady=8)
        self.text_input.insert('1.0', 'print("Hello, World!")')

        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=8)

        self.btn_start = ctk.CTkButton(btn_frame, text="开始测试", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                                         corner_radius=10, command=self._start_test)
        self.btn_start.pack(side='left', padx=(0, 8))

        self.btn_stop = ctk.CTkButton(btn_frame, text="停止", fg_color='#EF4444', hover_color='#dc2626',
                                        corner_radius=10, command=self._stop_test, state="disabled")
        self.btn_stop.pack(side='left')

        self.status_label = ctk.CTkLabel(self, text="准备就绪", text_color=TEXT_PRIMARY)
        self.status_label.pack(pady=8)

    def _start_test(self):
        text = self.text_input.get('1.0', 'end').strip()
        if not text:
            return
        self.testing = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self._test_thread, args=(text,), daemon=True).start()

    def _test_thread(self, text):
        for i in range(3, 0, -1):
            if not self.testing:
                break
            self.after(0, lambda n=i: self.status_label.configure(text=f"倒计时: {n}..."))
            time.sleep(1)
        if self.testing:
            success = self.input_simulator.type_text(text)
            self.after(0, lambda: self.status_label.configure(text="✅ 输入完成" if success else "❌ 输入失败"))
        self.after(0, self._reset)

    def _stop_test(self):
        self.testing = False

    def _reset(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.testing = False
