import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

from path_config import CHROME_EXTENSION_PATH, CONFIG_DIR

logger = logging.getLogger(__name__)

CF_T_ENDPOINT = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
DEFAULT_LAUNCH_URL = "https://www.educoder.net/"


class ExtensionSetup:
    def __init__(self):
        self.extension_path = CHROME_EXTENSION_PATH

    def _report_progress(self, progress_callback, message):
        if callable(progress_callback):
            try:
                progress_callback(message)
            except Exception:
                logger.debug("进度回调失败: %s", message, exc_info=True)

    def _is_browser_running(self, browser="chrome"):
        """检查浏览器进程是否在运行"""
        try:
            if sys.platform == "win32":
                import ctypes

                ctypes.windll.kernel32.SetErrorMode(0x0001)  # SEM_FAILCRITICALERRORS
                process_name = "chrome.exe" if browser == "chrome" else "msedge.exe"
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return process_name in result.stdout.lower()
        except Exception:
            pass
        return False

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
                result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
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
            os.path.join(os.path.dirname(self.extension_path), "chrome"),
            os.path.join(os.getcwd(), "chrome", "chrome"),
            os.path.join(os.getcwd(), "chrome"),
        ]

        for path in search_paths:
            if path and os.path.isdir(path):
                manifest = os.path.join(path, "manifest.json")
                if os.path.exists(manifest):
                    return os.path.abspath(path)

        return os.path.abspath(self.extension_path)

    def get_chrome_path(self):
        """查找 Chrome 可执行文件路径"""
        if sys.platform == "win32":
            paths = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                )
                reg_path, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if reg_path and os.path.exists(reg_path):
                    return reg_path
            except Exception:
                pass
        elif sys.platform == "darwin":
            paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        else:
            paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def get_edge_path(self):
        """查找 Edge 可执行文件路径"""
        if sys.platform == "win32":
            paths = [
                os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            ]
        elif sys.platform == "darwin":
            paths = ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
        else:
            paths = ["/usr/bin/microsoft-edge", "/usr/bin/microsoft-edge-stable"]

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _get_runtime_root(self):
        runtime_root = Path(CONFIG_DIR) / "browser_runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        return runtime_root

    def get_chrome_for_testing_dir(self):
        cft_dir = self._get_runtime_root() / "chrome_for_testing"
        cft_dir.mkdir(parents=True, exist_ok=True)
        return cft_dir

    def get_chrome_for_testing_binary(self):
        cft_dir = self.get_chrome_for_testing_dir()
        if sys.platform == "win32":
            candidates = list(cft_dir.glob("chrome-*/chrome-win*/chrome.exe"))
        elif sys.platform == "darwin":
            candidates = list(cft_dir.glob("chrome-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"))
        else:
            candidates = list(cft_dir.glob("chrome-*/chrome-linux64/chrome"))

        if not candidates:
            return None
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return str(candidates[0])

    def _get_cft_platform_key(self):
        if sys.platform == "win32":
            return "win64" if sys.maxsize > 2**32 else "win32"
        if sys.platform == "darwin":
            return "mac-arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "mac-x64"
        return "linux64"

    def _fetch_cft_metadata(self, progress_callback=None):
        self._report_progress(progress_callback, "正在获取 Chrome for Testing 下载信息...")
        response = requests.get(CF_T_ENDPOINT, timeout=30)
        response.raise_for_status()
        data = response.json()

        downloads = data.get("channels", {}).get("Stable", {}).get("downloads", {}).get("chrome", [])
        platform_key = self._get_cft_platform_key()
        for item in downloads:
            if item.get("platform") == platform_key:
                return {
                    "version": data.get("channels", {}).get("Stable", {}).get("version"),
                    "url": item.get("url"),
                    "platform": platform_key,
                }
        raise RuntimeError(f"Chrome for Testing 当前未提供平台包: {platform_key}")

    def ensure_chrome_for_testing(self, progress_callback=None):
        existing_binary = self.get_chrome_for_testing_binary()
        if existing_binary and os.path.exists(existing_binary):
            self._report_progress(progress_callback, "已找到本地 Chrome for Testing 缓存，跳过下载")
            return existing_binary, False

        metadata = self._fetch_cft_metadata(progress_callback=progress_callback)
        version = metadata.get("version")
        download_url = metadata.get("url")
        if not version or not download_url:
            raise RuntimeError("Chrome for Testing 下载信息不完整")

        target_root = self.get_chrome_for_testing_dir() / f"chrome-{version}"
        binary_path = self._get_cft_binary_in_dir(target_root)
        if binary_path and binary_path.exists():
            self._report_progress(progress_callback, f"Chrome for Testing {version} 已缓存，准备启动")
            return str(binary_path), False

        if target_root.exists():
            shutil.rmtree(target_root, ignore_errors=True)
        target_root.mkdir(parents=True, exist_ok=True)

        archive_path = self.get_chrome_for_testing_dir() / f"chrome-{version}.zip"
        self._report_progress(progress_callback, f"开始下载 Chrome for Testing {version}...")
        self._download_file(download_url, archive_path, progress_callback=progress_callback)

        try:
            self._report_progress(progress_callback, "下载完成，正在解压 Chrome for Testing...")
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(target_root)
        except zipfile.BadZipFile as exc:
            shutil.rmtree(target_root, ignore_errors=True)
            raise RuntimeError(f"Chrome for Testing 压缩包损坏: {exc}") from exc
        finally:
            archive_path.unlink(missing_ok=True)

        binary_path = self._get_cft_binary_in_dir(target_root)
        if not binary_path or not binary_path.exists():
            raise RuntimeError("Chrome for Testing 解压完成，但未找到可执行文件")
        self._report_progress(progress_callback, "Chrome for Testing 解压完成")
        return str(binary_path), True

    def _get_cft_binary_in_dir(self, root_dir):
        root_path = Path(root_dir)
        if sys.platform == "win32":
            candidate = root_path / "chrome-win64" / "chrome.exe"
            if not candidate.exists():
                candidate = root_path / "chrome-win32" / "chrome.exe"
        elif sys.platform == "darwin":
            candidate = (
                root_path
                / "chrome-mac"
                / "Google Chrome for Testing.app"
                / "Contents"
                / "MacOS"
                / "Google Chrome for Testing"
            )
        else:
            candidate = root_path / "chrome-linux64" / "chrome"
        return candidate if candidate.exists() else None

    def _download_file(self, url, target_path, progress_callback=None):
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", "0") or 0)
            downloaded = 0
            last_percent = -1
            with open(target_path, "wb") as file_obj:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file_obj.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = min(100, int(downloaded * 100 / total_size))
                            if percent != last_percent and (percent == 100 or percent - last_percent >= 5):
                                last_percent = percent
                                self._report_progress(progress_callback, f"正在下载 Chrome for Testing... {percent}%")
                        elif downloaded == len(chunk):
                            self._report_progress(progress_callback, "正在下载 Chrome for Testing...")

    def _ensure_extension_source(self):
        extension_dir = self.get_extension_dir()
        manifest_file = os.path.join(extension_dir, "manifest.json")
        if not os.path.isdir(extension_dir):
            raise FileNotFoundError(f"扩展目录不存在: {extension_dir}")
        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"manifest.json 不存在: {manifest_file}")
        return extension_dir

    def _prepare_extension_dir(self, progress_callback=None):
        self._report_progress(progress_callback, "正在校验扩展目录...")
        extension_dir = self._ensure_extension_source()
        temp_ext_dir = tempfile.mkdtemp(prefix="learning_assistant_ext_", dir=str(self._get_runtime_root()))
        shutil.copytree(extension_dir, os.path.join(temp_ext_dir, "extension"))
        self._report_progress(progress_callback, "扩展文件已准备完成")
        return os.path.join(temp_ext_dir, "extension")

    def _create_profile_dir(self, browser_name):
        return tempfile.mkdtemp(prefix=f"learning_assistant_{browser_name}_profile_", dir=str(self._get_runtime_root()))

    def _launch_browser_process(self, browser_path, extension_dir, browser_name, url=None, extra_args=None):
        if not browser_path or not os.path.exists(browser_path):
            raise FileNotFoundError(f"未找到 {browser_name} 浏览器")

        profile_dir = self._create_profile_dir(browser_name.lower())
        target_url = url or DEFAULT_LAUNCH_URL
        cmd = [
            browser_path,
            f"--load-extension={extension_dir}",
            f"--disable-extensions-except={extension_dir}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
            target_url,
        ]
        if extra_args:
            cmd[1:1] = extra_args
        subprocess.Popen(cmd)
        logger.info("%s 已启动并加载扩展: %s", browser_name, browser_path)

    def _launch_edge_simple(self, url=None, progress_callback=None):
        edge_path = self.get_edge_path()
        if not edge_path:
            return False, "未找到 Edge 浏览器"

        extension_dir = self._prepare_extension_dir(progress_callback=progress_callback)
        try:
            self._report_progress(progress_callback, "正在启动 Edge...")
            self._launch_browser_process(edge_path, extension_dir, "Edge", url=url)
            return True, "Edge 已启动并加载扩展"
        except Exception as exc:
            logger.warning("Edge 简单启动失败: %s", exc)
            return False, f"启动 Edge 失败: {exc}"

    def launch_with_extension_selenium(self, browser="edge", url=None, progress_callback=None):
        """Selenium 仅作为 Edge 自动安装兜底。"""
        if browser != "edge":
            raise RuntimeError("Selenium 兜底仅支持 Edge")

        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
        except ImportError as exc:
            raise ImportError("需要安装 selenium: pip install selenium") from exc

        edge_path = self.get_edge_path()
        if not edge_path:
            raise FileNotFoundError("未找到 Edge 浏览器")

        extension_dir = self._prepare_extension_dir(progress_callback=progress_callback)
        edge_options = EdgeOptions()
        edge_options.binary_location = edge_path
        edge_options.add_argument(f"--load-extension={extension_dir}")
        edge_options.add_argument(f"--disable-extensions-except={extension_dir}")
        edge_options.add_argument(f"--user-data-dir={self._create_profile_dir('edge_selenium')}")
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        edge_options.add_experimental_option("detach", True)

        self._report_progress(progress_callback, "正在通过 Selenium 启动 Edge...")
        driver = webdriver.Edge(options=edge_options)
        driver.get(url or DEFAULT_LAUNCH_URL)
        logger.info("Edge 已启动并加载扩展（Selenium）")
        return True, "Edge 已启动并加载扩展"

    def launch_chrome_for_testing(self, url=None, progress_callback=None):
        extension_dir = self._prepare_extension_dir(progress_callback=progress_callback)
        chrome_binary, downloaded = self.ensure_chrome_for_testing(progress_callback=progress_callback)
        self._report_progress(progress_callback, "正在启动 Chrome for Testing...")
        self._launch_browser_process(chrome_binary, extension_dir, "Chrome for Testing", url=url)
        if downloaded:
            return True, "Chrome for Testing 已下载并启动，扩展已自动加载"
        return True, "Chrome for Testing 已启动，扩展已自动加载"

    def launch_with_extension(self, browser="chrome", url=None, progress_callback=None):
        """Chrome 使用 Chrome for Testing，Edge 使用本机 Edge。"""
        try:
            if browser == "chrome":
                return self.launch_chrome_for_testing(url=url, progress_callback=progress_callback)

            success, message = self._launch_edge_simple(url=url, progress_callback=progress_callback)
            if success:
                return success, message

            logger.warning("Edge 简单启动失败，尝试 Selenium 模式: %s", message)
            self._report_progress(progress_callback, "Edge 普通启动失败，正在尝试 Selenium 方式...")
            return self.launch_with_extension_selenium(browser="edge", url=url, progress_callback=progress_callback)
        except requests.RequestException as exc:
            logger.warning("Chrome for Testing 下载失败: %s", exc)
            return False, f"下载 Chrome for Testing 失败: {exc}。请检查网络后重试，或改用手动安装。"
        except Exception as exc:
            logger.warning("启动浏览器失败: %s", exc)
            return False, f"启动失败: {exc}"

    def _open_browser_internal_page(self, browser_path, internal_url):
        subprocess.Popen([browser_path, "--new-window", internal_url])

    def _fallback_open_internal_page(self, internal_url):
        if sys.platform == "win32":
            subprocess.Popen(["cmd", "/c", "start", "", internal_url])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", internal_url])
        else:
            subprocess.Popen(["xdg-open", internal_url])

    def _open_extension_page(self, browser_name, browser_path, internal_url):
        if browser_path and os.path.exists(browser_path):
            try:
                self._open_browser_internal_page(browser_path, internal_url)
                return True, f"已打开 {browser_name} 扩展管理页面"
            except Exception as exc:
                logger.warning("%s 扩展页直接打开失败，尝试协议回退: %s", browser_name, exc)

        try:
            self._fallback_open_internal_page(internal_url)
            return True, f"已通过系统协议打开 {browser_name} 扩展管理页面"
        except Exception as exc:
            return False, f"打开 {browser_name} 扩展管理页面失败: {exc}"

    def open_chrome_extensions(self):
        """打开 Chrome 扩展管理页面"""
        return self._open_extension_page("Chrome", self.get_chrome_path(), "chrome://extensions/")

    def open_edge_extensions(self):
        """打开 Edge 扩展管理页面"""
        return self._open_extension_page("Edge", self.get_edge_path(), "edge://extensions/")

    def open_extension_folder(self):
        """打开扩展文件夹"""
        try:
            abs_path = self._ensure_extension_source()
            if sys.platform == "win32":
                subprocess.Popen(["explorer", abs_path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])
            return True, f"已打开扩展文件夹: {abs_path}"
        except Exception as exc:
            return False, f"打开失败: {exc}"
