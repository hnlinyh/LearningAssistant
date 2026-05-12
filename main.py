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
    """直接创建 .env 文件，包含默认配置"""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("""# AI 模型配置
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=

# 服务器配置
WS_HOST=localhost
WS_PORT=8001

# OCR 服务配置
OCR_API_URL=https://ocr.yhsun.cn/
""")

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
