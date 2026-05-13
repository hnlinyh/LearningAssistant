import asyncio
import http
import json
import logging
import os
import threading
import websockets
from path_config import PROJECT_ROOT

logger = logging.getLogger(__name__)

class ServerManager:
    def __init__(self, gui, model_info=None, host=None, port=None):
        self.gui = gui
        self.model_info = model_info or {}
        self.server_running = False
        self.server_thread = None
        self.websocket_server = None
        self.host = host or os.getenv('WS_HOST', 'localhost')
        self.port = port or int(os.getenv('WS_PORT', '8000'))
        self.assistant = None
        self._server_loop = None

    def start(self):
        if self.server_running:
            return
        self.server_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        if self.gui:
            self.gui.log_message(f"WebSocket 服务器已启动 ws://{self.host}:{self.port}")

    def stop(self):
        self.server_running = False
        if self.assistant:
            self.assistant.reset()
        if self.gui:
            self.gui.log_message("WebSocket 服务器已停止")

    def _run_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._server_loop = loop
        loop.run_until_complete(self._start_websocket_server())

    async def _process_request(self, connection, request):
        """处理 HTTP 发现请求，返回 WebSocket 地址。"""
        if request.path == '/discover':
            body = json.dumps({"ws_port": self.port, "ws_url": f"ws://{self.host}:{self.port}"})
            return connection.respond(http.HTTPStatus.OK, body)
        return None

    async def _start_websocket_server(self):
        from core.assistant import LearningAssistant
        self.assistant = LearningAssistant(self.gui, self.model_info)

        try:
            async with websockets.serve(
                self._handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=60,
                process_request=self._process_request,
            ) as server:
                self.websocket_server = server
                while self.server_running:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
            if self.gui:
                self.gui.log_message(f"服务器错误: {e}")

    async def _handler(self, websocket):
        try:
            await self.assistant.server(websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Handler error: {e}")

    def update_model(self, model_info):
        self.model_info = model_info
        if self.assistant:
            self.assistant.update_model(model_info)

    def set_language(self, lang):
        if self.assistant:
            self.assistant.set_language(lang)

    def broadcast_config(self, config):
        """广播配置到所有连接的客户端"""
        if self.assistant:
            loop = self._server_loop
            if loop:
                asyncio.run_coroutine_threadsafe(
                    self.assistant.broadcast_to_clients({
                        "type": "sync_input_config",
                        "config": config
                    }),
                    loop
                )
