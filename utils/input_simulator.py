import platform
import time
import threading
import logging
import pyperclip
import pyautogui

logger = logging.getLogger(__name__)

class InputSimulator:
    def __init__(self, gui=None):
        self.gui = gui
        self.typing_active = True
        self.esc_pressed = False
        self.is_linux = platform.system() == "Linux"
        self.xdotool_available = self._check_xdotool()

    def _check_xdotool(self):
        if not self.is_linux:
            return False
        try:
            import subprocess
            subprocess.run(['xdotool', '--version'], capture_output=True)
            return True
        except Exception:
            return False

    def _write_text(self, text):
        if self.is_linux and self.xdotool_available:
            import subprocess
            for char in text:
                subprocess.run(['xdotool', 'type', '--delay', '1', char])
        else:
            try:
                import keyboard
                keyboard.write(text)
            except Exception:
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')

    def _press_key(self, key):
        if self.is_linux and self.xdotool_available:
            import subprocess
            subprocess.run(['xdotool', 'key', key])
        else:
            try:
                import keyboard
                keyboard.press_and_release(key)
            except Exception:
                pyautogui.press(key)

    def _install_esc_hook(self):
        self.esc_pressed = False
        try:
            import keyboard
            keyboard.on_press_key('esc', lambda _: self._on_esc())
        except Exception:
            pass

    def _on_esc(self):
        self.esc_pressed = True
        self.typing_active = False

    def _remove_esc_hook(self):
        try:
            import keyboard
            keyboard.unhook_key('esc')
        except Exception:
            pass

    def _clear_editor_before_input(self):
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.1)

    def reset(self):
        self.typing_active = True
        self.esc_pressed = False

    def paste_code(self, code):
        try:
            self._install_esc_hook()
            screen_w, screen_h = pyautogui.size()
            pyautogui.click(screen_w // 2, screen_h // 2)
            time.sleep(0.3)
            self._clear_editor_before_input()
            time.sleep(0.2)
            pyperclip.copy(code)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            self._remove_esc_hook()
            return True
        except Exception as e:
            logger.error(f"Paste failed: {e}")
            try:
                self._write_text(code)
                self._remove_esc_hook()
                return True
            except Exception:
                return False

    def simulate_typing(self, text, delay=0.03, on_progress=None):
        try:
            self._install_esc_hook()
            screen_w, screen_h = pyautogui.size()
            pyautogui.click(screen_w // 2, screen_h // 2)
            time.sleep(0.3)
            self._clear_editor_before_input()
            time.sleep(0.2)
            lines = text.split('\n')
            total = len(lines)
            for i, line in enumerate(lines):
                if self.esc_pressed or not self.typing_active:
                    return False
                self._write_text(line)
                if i < total - 1:
                    self._press_key('enter')
                if on_progress:
                    on_progress(int((i + 1) / total * 100))
                time.sleep(delay)
            self._remove_esc_hook()
            return True
        except Exception as e:
            logger.error(f"Typing simulation failed: {e}")
            self._remove_esc_hook()
            return False

    def type_text(self, text):
        try:
            if self.gui:
                self.gui.log_message("3 秒后开始输入，请切换到目标窗口...")
            for i in range(3, 0, -1):
                if self.gui:
                    self.gui.log_message(f"倒计时: {i}...")
                time.sleep(1)
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            return True
        except Exception as e:
            logger.error(f"Direct input failed: {e}")
            try:
                import keyboard
                keyboard.write(text)
                return True
            except Exception:
                return False
