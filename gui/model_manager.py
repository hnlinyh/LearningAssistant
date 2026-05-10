import time
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, gui):
        self.gui = gui
        self.all_models = []

    async def fetch_models(self, api_key, base_url):
        """Call API GET /models to fetch available model list"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            response = await client.models.list()
            models = [m.id for m in response.data if hasattr(m, 'id')]
            self.all_models = sorted(models)
            return self.all_models
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            if self.gui:
                self.gui.log_message(f"获取模型失败: {e}")
            return []

    async def test_model(self, api_key, base_url, model_name):
        """Test model connectivity, return {success, latency, error}"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            start = time.time()
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=10,
                temperature=0
            )
            latency = time.time() - start
            return {"success": True, "latency": latency}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def filter_models(self, keyword):
        """Filter model list by keyword"""
        if not keyword:
            return self.all_models
        return [m for m in self.all_models if keyword.lower() in m.lower()]
