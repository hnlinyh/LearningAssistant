import os
import sys
import subprocess
import tempfile
import shutil
import logging
import socket
import platform
from path_config import CHROME_EXTENSION_PATH

logger = logging.getLogger(__name__)

# 单实例锁端口
_INSTANCE_LOCK_PORT = 48573
_INSTANCE_LOCK_SOCKET = None


class ExtensionSetup:
    def __init__(self):
        self.extension_path = CHROME_EXTENSION_PATH
        self._lock_socket = None

    def _acquire_single_instance_lock(self):
        """获取单实例锁，防止重复启动"""
        global _INSTANCE_LOCK_SOCKET
        if _INSTANCE_LOCK_SOCKET is not None:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", _INSTANCE_LOCK_PORT))
            sock.listen(1)
            _INSTANCE_LOCK_SOCKET = sock
            self._lock_socket = sock
            return True
        except OSError:
            return False

    def _release_single_instance_lock(self):
        """释放单实例锁"""
        global _INSTANCE_LOCK_SOCKET
        if _INSTANCE_LOCK_SOCKET is not None:
            try:
                _INSTANCE_LOCK_SOCKET.close()
            except Exception:
                pass
            _INSTANCE_LOCK_SOCKET = None
            self._lock_socket = None

    def get_chrome_version(self):
        """获取 Chrome 版本号"""
        if platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                return version
            except Exception:
                pass
        else:
            try:
                result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1]
            except Exception:
                pass
        return None

    def get_edge_version(self):
        """获取 Edge 版本号"""
        if platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                return version
            except Exception:
                pass
        return None

    def get_extension_dir(self):
        """查找扩展目录（包含 manifest.json）"""
        search_paths = [
            self.extension_path,
            os.path.join(os.path.dirname(self.extension_path), 'chrome'),
            os.path.join(os.getcwd(), 'chrome', 'chrome'),
            os.path.join(os.getcwd(), 'chrome'),
        ]

        for path in search_paths:
            if path and os.path.isdir(path):
                manifest = os.path.join(path, 'manifest.json')
                if os.path.exists(manifest):
                    return os.path.abspath(path)

        return os.path.abspath(self.extension_path)

    def get_chrome_path(self):
        """查找 Chrome 可执行文件路径"""
        if sys.platform == 'win32':
            paths = [
                os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
            ]
            # 尝试从注册表 App Paths 查找
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
                reg_path, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if reg_path and os.path.exists(reg_path):
                    return reg_path
            except Exception:
                pass
        elif sys.platform == 'darwin':
            paths = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
        else:
            paths = ['/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/usr/bin/chromium']

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def get_edge_path(self):
        """查找 Edge 可执行文件路径"""
        if sys.platform == 'win32':
            paths = [
                os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
                os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
            ]
        elif sys.platform == 'darwin':
            paths = ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge']
        else:
            paths = ['/usr/bin/microsoft-edge', '/usr/bin/microsoft-edge-stable']

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def launch_with_extension_selenium(self, browser='chrome', url=None):
        """使用 Selenium WebDriver 启动浏览器并加载扩展"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.edge.options import Options as EdgeOptions
        except ImportError:
            raise ImportError("需要安装 selenium: pip install selenium")

        extension_dir = self.get_extension_dir()
        manifest_file = os.path.join(extension_dir, 'manifest.json')

        if not os.path.exists(extension_dir) or not os.path.exists(manifest_file):
            raise FileNotFoundError(f"扩展目录或 manifest.json 不存在: {extension_dir}")

        # 复制到临时目录避免中文路径问题
        temp_ext_dir = os.path.join(tempfile.gettempdir(), 'learning_assistant_ext')
        if os.path.exists(temp_ext_dir):
            shutil.rmtree(temp_ext_dir)
        shutil.copytree(extension_dir, temp_ext_dir)

        if browser == 'edge':
            return self._launch_edge_selenium(temp_ext_dir, url)
        else:
            return self._launch_chrome_selenium(temp_ext_dir, url)

    def _launch_chrome_selenium(self, extension_dir, url=None):
        """使用 Selenium 启动 Chrome"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        chrome_options = ChromeOptions()
        chrome_options.add_argument(f'--load-extension={extension_dir}')
        chrome_options.add_argument(f'--disable-extensions-except={extension_dir}')
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option("detach", True)

        # 使用 Selenium Manager 自动下载匹配的 chromedriver
        driver = webdriver.Chrome(options=chrome_options)

        if url:
            driver.get(url)
        else:
            driver.get('https://www.educoder.net/')

        logger.info("Chrome 已启动并加载扩展（Selenium）")
        return True, "Chrome 已启动并加载扩展"

    def _launch_edge_selenium(self, extension_dir, url=None):
        """使用 Selenium 启动 Edge"""
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions

        edge_options = EdgeOptions()
        edge_options.add_argument(f'--load-extension={extension_dir}')
        edge_options.add_argument('--enable-extensions')
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        edge_options.add_experimental_option("detach", True)

        driver = webdriver.Edge(options=edge_options)

        if url:
            driver.get(url)
        else:
            driver.get('https://www.educoder.net/')

        logger.info("Edge 已启动并加载扩展（Selenium）")
        return True, "Edge 已启动并加载扩展"

    def launch_with_extension_simple(self, browser='chrome', url=None):
        """简单启动方式（回退方案）"""
        def _launch(browser_path, browser_name):
            abs_ext_path = os.path.abspath(self.extension_path)
            temp_ext_dir = os.path.join(tempfile.gettempdir(), 'learning_assistant_ext')
            if os.path.exists(temp_ext_dir):
                shutil.rmtree(temp_ext_dir)
            shutil.copytree(abs_ext_path, temp_ext_dir)
            cmd = [
                browser_path,
                f'--load-extension={temp_ext_dir}',
                '--no-first-run',
                '--no-default-browser-check',
            ]
            if url:
                cmd.append(url)
            subprocess.Popen(cmd)
            logger.info(f"{browser_name} 已启动（简单模式）")

        if browser == 'edge':
            edge_path = self.get_edge_path()
            if not edge_path:
                return False, "未找到 Edge 浏览器"
            try:
                _launch(edge_path, "Edge")
                return True, "Edge 已启动并加载扩展"
            except Exception as e:
                return False, f"启动 Edge 失败: {e}"
        else:
            chrome_path = self.get_chrome_path()
            if chrome_path:
                try:
                    _launch(chrome_path, "Chrome")
                    return True, "Chrome 已启动并加载扩展"
                except Exception as e:
                    edge_path = self.get_edge_path()
                    if edge_path:
                        try:
                            _launch(edge_path, "Edge")
                            return True, "Chrome 启动失败，已改用 Edge"
                        except Exception as e2:
                            return False, f"启动失败: {e2}"
                    return False, f"Chrome 启动失败且未找到 Edge: {e}"
            else:
                edge_path = self.get_edge_path()
                if not edge_path:
                    return False, "未找到 Chrome 或 Edge 浏览器"
                try:
                    _launch(edge_path, "Edge")
                    return True, "未找到 Chrome，已改用 Edge"
                except Exception as e:
                    return False, f"启动 Edge 失败: {e}"

    def launch_with_extension(self, browser='chrome', url=None):
        """启动浏览器并加载扩展（优先使用 Selenium，回退到简单模式）"""
        if not self._acquire_single_instance_lock():
            logger.warning("已有浏览器实例在运行")
            return False, "已有浏览器实例在运行，请先关闭"

        try:
            return self.launch_with_extension_selenium(browser, url)
        except ImportError:
            logger.warning("selenium 未安装，使用简单启动模式")
            return self.launch_with_extension_simple(browser, url)
        except Exception as e:
            logger.warning(f"Selenium 启动失败: {e}，使用简单启动模式")
            return self.launch_with_extension_simple(browser, url)

    def open_chrome_extensions(self):
        """打开 Chrome 扩展管理页面"""
        chrome_path = self.get_chrome_path()
        if chrome_path:
            subprocess.Popen([chrome_path, 'chrome://extensions'])
            return True
        return False

    def open_edge_extensions(self):
        """打开 Edge 扩展管理页面"""
        edge_path = self.get_edge_path()
        if edge_path:
            subprocess.Popen([edge_path, 'edge://extensions'])
            return True
        return False

    def open_extension_folder(self):
        """打开扩展文件夹"""
        try:
            abs_path = os.path.abspath(self.extension_path)
            if not os.path.isdir(abs_path):
                return False, "扩展文件夹不存在"

            if sys.platform == 'win32':
                subprocess.Popen(['explorer', abs_path])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', abs_path])
            else:
                subprocess.Popen(['xdg-open', abs_path])
            return True, "已打开扩展文件夹"
        except Exception as e:
            return False, f"打开失败: {e}"
