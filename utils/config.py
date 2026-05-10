import configparser
import os
import uuid
from pathlib import Path


class ConfigManager:
    # .env 文件路径：项目根目录
    _env_path = str(Path(__file__).resolve().parent.parent / '.env')

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_dir = os.path.join(os.path.expanduser('~'), '.learning_assistant')
        self.config_path = os.path.join(self.config_dir, 'config.ini')
        os.makedirs(self.config_dir, exist_ok=True)
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
        if not self.config.has_section('SETTINGS'):
            self.config.add_section('SETTINGS')

    def get_setting(self, key, default=None, section='SETTINGS'):
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def save_setting(self, key, value, section='SETTINGS'):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_machine_code(self):
        code = self.get_setting('machine_code')
        if not code:
            code = uuid.uuid4().hex[:16].upper()
            self.save_setting('machine_code', code)
        return code

    # ========== .env 文件持久化 ==========

    @classmethod
    def save_to_env(cls, data: dict):
        """将键值对保存到 .env 文件，保留已有注释和其他配置项。"""
        env_path = cls._env_path
        lines = []
        existing_keys = set()

        # 读取现有 .env 文件内容
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # 解析已有键
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                key = stripped.split('=', 1)[0].strip()
                if key:
                    existing_keys.add(key)

        # 更新已有键的值
        for key, value in data.items():
            value_str = str(value) if value is not None else ''
            if key in existing_keys:
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        k = stripped.split('=', 1)[0].strip()
                        if k == key:
                            lines[i] = f'{key}={value_str}\n'
                            break
            else:
                # 新键追加到文件末尾
                if lines and not lines[-1].endswith('\n'):
                    lines.append('\n')
                lines.append(f'{key}={value_str}\n')

        # 确保目录存在
        os.makedirs(os.path.dirname(env_path), exist_ok=True)

        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    @classmethod
    def load_from_env(cls) -> dict:
        """从 .env 文件读取配置，返回键值对字典。"""
        env_path = cls._env_path
        result = {}
        if not os.path.exists(env_path):
            return result
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    if '=' in stripped:
                        key, value = stripped.split('=', 1)
                        result[key.strip()] = value.strip()
        return result
