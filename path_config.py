"""路径配置模块 - 确保项目根目录在 sys.path 中"""
import os
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 将项目根目录添加到 sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导出路径常量
CHROME_EXTENSION_PATH = os.path.join(PROJECT_ROOT, 'chrome', 'chrome')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.learning_assistant')
