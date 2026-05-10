import customtkinter as ctk
import json
import os

PRIMARY = '#4F6BED'
PRIMARY_DARK = '#3B52CC'
BG = '#F8FAFC'
TEXT_PRIMARY = '#1E293B'
BORDER = '#E2E8F0'

BUILTIN_LANGUAGES = ["C", "C++", "Java", "Python", "JavaScript", "C#"]

class LanguageManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.languages = list(BUILTIN_LANGUAGES)
        self._load_custom()

    def _load_custom(self):
        saved = self.config_manager.get_setting('custom_languages', '[]')
        try:
            custom = json.loads(saved)
            for lang in custom:
                if lang not in self.languages:
                    self.languages.append(lang)
        except Exception:
            pass

    def _save_custom(self):
        custom = [l for l in self.languages if l not in BUILTIN_LANGUAGES]
        self.config_manager.save_setting('custom_languages', json.dumps(custom))

    def add_language(self, name):
        name = name.strip()
        if name and name not in self.languages:
            self.languages.append(name)
            self._save_custom()
            return True
        return False

    def remove_language(self, name):
        if name in BUILTIN_LANGUAGES:
            return False
        if name in self.languages:
            self.languages.remove(name)
            self._save_custom()
            return True
        return False

    def get_languages(self):
        return list(self.languages)


class LanguageManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, language_manager):
        super().__init__(parent)
        self.title("语言管理")
        self.geometry("360x400")
        self.configure(fg_color=BG)
        self.lm = language_manager

        ctk.CTkLabel(self, text="语言管理", font=("", 16, "bold"), text_color=TEXT_PRIMARY).pack(pady=(16, 8))

        # Add language
        add_frame = ctk.CTkFrame(self, fg_color='transparent')
        add_frame.pack(fill='x', padx=16, pady=4)
        self.new_lang_entry = ctk.CTkEntry(add_frame, placeholder_text="输入语言名称", fg_color='white',
                                            border_color=BORDER, corner_radius=8)
        self.new_lang_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ctk.CTkButton(add_frame, text="添加", fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                       corner_radius=8, width=60, command=self._add).pack(side='left')

        # List
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color='white', corner_radius=10, border_width=1, border_color=BORDER)
        self.list_frame.pack(fill='both', expand=True, padx=16, pady=8)
        self._refresh()

    def _refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        for lang in self.lm.get_languages():
            row = ctk.CTkFrame(self.list_frame, fg_color='transparent')
            row.pack(fill='x', padx=4, pady=2)
            ctk.CTkLabel(row, text=lang, text_color=TEXT_PRIMARY).pack(side='left', padx=8)
            if lang not in ['C', 'C++', 'Java', 'Python', 'JavaScript', 'C#']:
                ctk.CTkButton(row, text="删除", fg_color='#EF4444', hover_color='#dc2626',
                               corner_radius=6, width=50, height=24,
                               command=lambda l=lang: self._remove(l)).pack(side='right', padx=4)

    def _add(self):
        name = self.new_lang_entry.get().strip()
        if self.lm.add_language(name):
            self.new_lang_entry.delete(0, 'end')
            self._refresh()

    def _remove(self, name):
        self.lm.remove_language(name)
        self._refresh()
