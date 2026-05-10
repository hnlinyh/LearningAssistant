import os
import sys
import shutil
import logging
from dotenv import load_dotenv

# 导入路径配置
from path_config import PROJECT_ROOT

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'learning_assistant.log'), encoding='utf-8')
    ]
)

def ensure_env():
    """Copy .env.example to .env if .env doesn't exist"""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    env_example = os.path.join(PROJECT_ROOT, '.env.example')
    if not os.path.exists(env_path) and os.path.exists(env_example):
        shutil.copy2(env_example, env_path)

def main():
    ensure_env()
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

    import customtkinter as ctk
    from gui.main_window import MainWindow

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
