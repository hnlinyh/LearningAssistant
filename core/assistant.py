import os
import json
import re
import logging
import asyncio
from openai import AsyncOpenAI
from utils.input_simulator import InputSimulator

logger = logging.getLogger(__name__)

class LearningAssistant:
    def __init__(self, gui, model_info=None):
        self.gui = gui
        self.model_info = model_info or {}
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model_name = self.model_info.get('model', os.getenv('OPENAI_MODEL', 'qwen3-coder-plus'))

        # 详细的配置日志
        logger.info(f"环境变量 OPENAI_API_KEY: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else '***'}" if self.api_key else "环境变量 OPENAI_API_KEY: 未设置")
        logger.info(f"环境变量 OPENAI_BASE_URL: {self.base_url}")
        logger.info(f"环境变量 OPENAI_MODEL: {self.model_name}")

        self.client = None
        self._init_client()
        self.input_simulator = InputSimulator(gui)
        self.current_language = 'python'
        self.last_question = ''
        self.last_code = ''
        self.retry_count = 0
        self.max_retries = 3
        self.progress = 0

    def _init_client(self):
        api_key = self.model_info.get('api_key', self.api_key)
        base_url = self.model_info.get('base_url', self.base_url)
        logger.info(f"初始化客户端: base_url={base_url}, api_key={'*' * 8 if api_key else '未设置'}")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            logger.info("OpenAI 客户端初始化成功")
        else:
            logger.warning("API Key 未设置，客户端初始化失败")

    def set_language(self, lang):
        self.current_language = lang.lower()

    def reset(self):
        self.last_question = ''
        self.last_code = ''
        self.retry_count = 0
        self.progress = 0

    def update_model(self, model_info):
        self.model_info = model_info
        self.model_name = model_info.get('model', self.model_name)
        self.api_key = model_info.get('api_key', self.api_key)
        self.base_url = model_info.get('base_url', self.base_url)
        self._init_client()

    async def server(self, websocket):
        # 连接成功时发送配置信息
        await websocket.send(json.dumps({
            "type": "config_info",
            "model": self.model_name
        }, ensure_ascii=False))

        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', '')
                if msg_type in ('content_auto_input', 'manual_question'):
                    await self.handle_content_auto_input(websocket, data)
                elif msg_type == 'test_results':
                    await self.handle_test_results(websocket, data)
                elif msg_type == 'ready_for_input':
                    await self.handle_ready_for_input(websocket, data)
                elif msg_type == 'direct_input_complete':
                    await self.handle_direct_input_complete(websocket, data)
                elif msg_type == 'progress_request':
                    await self.send_progress_update(websocket)
                elif msg_type == 'set_language':
                    lang = data.get('language', 'python')
                    self.set_language(lang)
                elif msg_type == 'sync_code':
                    await self.handle_sync_code(websocket, data)
                elif msg_type == 'simulate_input':
                    await self.handle_simulate_input(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
            except Exception as e:
                logger.error(f"Message handling error: {e}")
                await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    async def handle_sync_code(self, websocket, data):
        """接收扩展端同步的代码，显示在桌面端编辑器"""
        code = data.get('code', '')
        if code and self.gui:
            self.gui.set_code(code)
            await websocket.send(json.dumps({
                "type": "sync_code_ack",
                "status": "success"
            }))

    async def handle_simulate_input(self, websocket, data):
        """处理扩展端的模拟键盘输入请求"""
        import time
        code = data.get('code', '')
        if not code:
            await websocket.send(json.dumps({
                "type": "error", "message": "代码内容为空"
            }))
            return

        await websocket.send(json.dumps({
            "type": "server_ack", "message": "开始模拟输入..."
        }))

        # 在后台线程执行输入
        def do_input():
            try:
                self.input_simulator.reset()
                self.input_simulator.typing_active = True
                lines = code.split('\n')
                total = len(lines)
                for i, line in enumerate(lines):
                    if not self.input_simulator.typing_active:
                        break
                    self.input_simulator._write_text(line)
                    if i < total - 1:
                        self.input_simulator._press_key('enter')
                    progress = int((i + 1) / total * 100)
                    # 发送进度更新
                    asyncio.run(websocket.send(json.dumps({
                        "type": "progress_update", "progress": progress
                    })))
                    time.sleep(0.05)

                success = self.input_simulator.typing_active
                asyncio.run(websocket.send(json.dumps({
                    "type": "input_complete", "success": success
                })))
            except Exception as e:
                logger.error(f"Simulate input error: {e}")
                asyncio.run(websocket.send(json.dumps({
                    "type": "error", "message": str(e)
                })))

        import threading
        threading.Thread(target=do_input, daemon=True).start()

    async def handle_content_auto_input(self, websocket, data):
        question = data.get('question_content') or data.get('content') or data.get('problem_text', '')
        current_code = data.get('current_code') or data.get('existing_code') or data.get('editor_code', '')
        language = data.get('language') or data.get('lang') or data.get('programming_language', self.current_language)
        sync_question = data.get('sync_question', True)  # 默认同步题目到桌面端

        if language:
            self.current_language = language.lower()

        self.last_question = question
        self.retry_count = 0

        # 根据标志位决定是否同步题目到桌面端
        if self.gui and sync_question:
            self.gui.set_question(question)

        await websocket.send(json.dumps({
            "type": "server_ack",
            "status": "processing",
            "message": "正在生成代码..."
        }, ensure_ascii=False))

        self.progress = 10
        code = await self.get_complete_code_solution(question, current_code)

        if code:
            self.last_code = code
            # 同步生成的代码到桌面端
            if self.gui:
                self.gui.set_code(code)
            await websocket.send(json.dumps({
                "type": "code_solution",
                "code": code,
                "language": self.current_language,
                "model_used": self.model_name
            }, ensure_ascii=False))
        else:
            msg = "请先在桌面端配置 API Key" if not self.client else "AI 未能生成有效代码"
            await websocket.send(json.dumps({
                "type": "error",
                "code": "ERR_AI_RESPONSE_INVALID",
                "message": msg
            }))

    async def handle_test_results(self, websocket, data):
        try:
            test_results = data.get('results', {})
            test_text = test_results.get('text', '')
            current_code = data.get('current_code') or data.get('existing_code') or data.get('currentCode', '')

            has_error = any(kw in test_text.lower() for kw in ['[failed]', '错误', '失败', 'error', 'fail'])

            if has_error:
                if self.retry_count >= self.max_retries:
                    await websocket.send(json.dumps({
                        "type": "test_results_response",
                        "success": True,
                        "has_failures": True,
                        "message": f"已达到最大重试次数({self.max_retries}次)"
                    }, ensure_ascii=False))
                    return

                self.retry_count += 1
                revised_code = await self._generate_revised_code(self.last_question, test_text, current_code)

                if revised_code:
                    self.last_code = revised_code
                    # 同步纠错后的代码到桌面端
                    if self.gui:
                        self.gui.set_code(revised_code)
                    await websocket.send(json.dumps({
                        "type": "code_revision",
                        "code": revised_code,
                        "revision_number": self.retry_count
                    }, ensure_ascii=False))
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "code": "ERR_AI_RESPONSE_INVALID",
                        "message": "纠错代码生成失败"
                    }))
            else:
                await websocket.send(json.dumps({
                    "type": "test_results_response",
                    "success": True,
                    "has_failures": False,
                    "message": "所有测试通过！"
                }, ensure_ascii=False))
        except Exception as e:
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    async def handle_ready_for_input(self, websocket, data):
        code = data.get('code', '')
        success = self.input_simulator.paste_code(code)
        await websocket.send(json.dumps({
            "type": "input_complete",
            "success": success,
            "method_used": "paste"
        }))

    async def handle_direct_input_complete(self, websocket, data):
        success = data.get('success', False)
        if self.gui:
            if success:
                self.gui.log_message("代码已成功写入编辑器")
            else:
                self.gui.log_message("页面内写入失败，尝试键盘模拟...")

    async def send_progress_update(self, websocket):
        await websocket.send(json.dumps({
            "type": "progress_update",
            "progress": self.progress,
            "stage": "generating"
        }))

    def _get_system_prompt(self):
        lang_map = {
            'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java',
            'cpp': 'C++', 'c': 'C', 'csharp': 'C#'
        }
        lang_name = lang_map.get(self.current_language, self.current_language.upper())
        return f"""你是一个专业的编程助手，负责生成{lang_name}代码。
重要规则：
1. 只返回纯代码，不要有任何解释、注释或额外文字
2. 绝对不要使用任何代码块标记
3. 代码必须完整且可运行
4. 如果用户提供了已有代码，已有代码是不可改动的既有内容，严格保留
5. 如果用户提供了已有代码，只能在原有代码基础上补充缺失部分
6. 必须返回完整最终代码文件"""

    def _get_retry_system_prompt(self):
        lang_map = {
            'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java',
            'cpp': 'C++', 'c': 'C', 'csharp': 'C#'
        }
        lang_name = lang_map.get(self.current_language, self.current_language.upper())
        return f"""你是一个专业的编程助手，负责根据测试失败信息修正{lang_name}代码。
重要规则：
1. 只返回纯代码，不要有任何解释、注释或额外文字
2. 绝对不要使用任何代码块标记
3. 代码必须完整且可运行
4. 必须返回完整最终代码文件，不能只返回局部补丁
5. 专注于修复已知的错误，确保代码通过所有测试。"""

    def clean_code_response(self, content):
        if not content:
            return ''
        pattern = r'```(?:[\w#+\-.]*)?\s*\n([\s\S]*?)```'
        blocks = re.findall(pattern, content)
        if blocks:
            return max(blocks, key=len).strip()
        lines = content.strip().split('\n')
        code_lines = [l for l in lines if not l.startswith('#') and not l.startswith('//') and not l.startswith('<!--')]
        return '\n'.join(code_lines).strip()

    def _is_complete_code(self, code, existing_code=''):
        if not code or len(code.strip()) < 20:
            return False
        return True

    async def get_complete_code_solution(self, question, existing_code=''):
        if not self.client:
            logger.error("代码生成失败: 客户端未初始化 (API Key 可能未设置)")
            return None

        logger.info(f"开始生成代码: model={self.model_name}, 题目长度={len(question)}")
        self.progress = 20
        prompt = f"题目要求：\n{question}\n"
        if existing_code:
            prompt += f"\n编辑器中已有代码（不可修改，必须保留）：\n{existing_code}\n"
            prompt += "\n请在已有代码基础上补充缺失部分，返回完整最终代码。"
        else:
            prompt += "\n请生成完整的代码解决方案。"

        self.progress = 40
        for attempt in range(2):
            try:
                temp = 0.3 if attempt == 0 else 0
                logger.info(f"API 调用尝试 {attempt + 1}/2, temperature={temp}")
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=8192,
                    temperature=temp,
                    stream=False
                )
                self.progress = 80

                if not response.choices:
                    logger.warning(f"API 返回空响应: {response}")
                    continue

                raw_content = response.choices[0].message.content
                logger.info(f"API 响应长度: {len(raw_content) if raw_content else 0}")

                if not raw_content:
                    logger.warning("API 响应内容为空")
                    continue

                code = self.clean_code_response(raw_content)
                logger.info(f"清理后代码长度: {len(code)}")

                if not code:
                    logger.warning("代码清理后为空")
                    continue

                if self._is_complete_code(code, existing_code):
                    logger.info("代码生成成功")
                    self.progress = 100
                    return code
                else:
                    logger.warning(f"代码完整性检查失败: 代码长度={len(code)}, 已有代码长度={len(existing_code) if existing_code else 0}")
            except Exception as e:
                logger.error(f"API 调用失败 (尝试 {attempt+1}): {type(e).__name__}: {e}")

        logger.error("代码生成失败: 所有尝试均失败")
        self.progress = 100
        return None

    async def _generate_revised_code(self, question, test_text, previous_code):
        if not self.client:
            return None
        self.progress = 10
        prompt = f"""题目要求：
{question}

之前的代码：
{previous_code}

测试失败信息：
{test_text}

请根据以上信息，修复代码中的错误，生成新的完整代码。
特别注意：
1. 仔细分析测试失败的原因
2. 修正之前代码中的错误
3. 确保新代码能够通过所有测试用例
4. 只返回纯代码，不要有任何解释
5. 必须返回完整最终代码文件

请生成修复后的完整代码："""

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self.progress = 20 + attempt * 30
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_retry_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=8192,
                    temperature=0.3 + attempt * 0.2,
                    stream=False
                )
                if response.choices:
                    code = self.clean_code_response(response.choices[0].message.content)
                    # 纠错场景只检查代码非空和最小长度，不比较与原代码的长度
                    if code and len(code.strip()) >= 20:
                        self.progress = 100
                        return code
                    logger.warning(f"纠错代码完整性检查失败 (尝试 {attempt+1})")
            except Exception as e:
                logger.error(f"Code revision failed (尝试 {attempt+1}): {e}")
        self.progress = 100
        return None

    async def generate_code_for_gui(self, question, existing_code=''):
        return await self.get_complete_code_solution(question, existing_code)
