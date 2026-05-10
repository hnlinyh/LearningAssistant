import customtkinter as ctk
import requests
import threading

PRIMARY = '#4F6BED'
PRIMARY_DARK = '#3B52CC'
BG = '#F8FAFC'
TEXT_PRIMARY = '#1E293B'
BORDER = '#E2E8F0'

CURRENT_VERSION = '1.0.0'

class UpdateWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("检查更新")
        self.geometry("400x300")
        self.configure(fg_color=BG)

        ctk.CTkLabel(self, text="检查更新", font=("", 16, "bold"), text_color=TEXT_PRIMARY).pack(pady=(16, 8))

        self.status_label = ctk.CTkLabel(self, text="正在检查更新...", text_color=TEXT_PRIMARY)
        self.status_label.pack(pady=8)

        self.changelog_text = ctk.CTkTextbox(self, fg_color='white', corner_radius=10, height=120,
                                              border_width=1, border_color=BORDER, state="disabled")
        self.changelog_text.pack(fill='x', padx=16, pady=8)

        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=16, pady=8)
        self.btn_update = ctk.CTkButton(btn_frame, text="立即更新", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                                          corner_radius=10, state="disabled")
        self.btn_update.pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_frame, text="稍后提醒", fg_color='transparent', border_width=1, border_color=BORDER,
                       corner_radius=10, text_color=TEXT_PRIMARY, command=self.destroy).pack(side='left')

        threading.Thread(target=self._check_update, daemon=True).start()

    def _check_update(self):
        try:
            resp = requests.get('https://api.github.com/repos/example/learning-assistant/releases/latest', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                latest = data.get('tag_name', '').lstrip('v')
                if latest and latest != CURRENT_VERSION:
                    self.after(0, lambda: self.status_label.configure(text=f"发现新版本: v{latest}"))
                    changelog = data.get('body', '无更新日志')
                    self.after(0, lambda: self._set_changelog(changelog))
                    self.after(0, lambda: self.btn_update.configure(state="normal"))
                else:
                    self.after(0, lambda: self.status_label.configure(text="✅ 已是最新版本"))
            else:
                self.after(0, lambda: self.status_label.configure(text="检查更新失败"))
        except Exception:
            self.after(0, lambda: self.status_label.configure(text="网络错误，无法检查更新"))

    def _set_changelog(self, text):
        self.changelog_text.configure(state="normal")
        self.changelog_text.delete('1.0', 'end')
        self.changelog_text.insert('1.0', text)
        self.changelog_text.configure(state="disabled")
