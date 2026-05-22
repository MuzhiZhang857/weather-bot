import os
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "weather_alert.txt"
        )
        
        self._validate_config()

    def _validate_config(self) -> None:
        if not self.api_key:
            logger.warning("LLM_API_KEY 未配置")
        if not self.base_url:
            logger.warning("LLM_BASE_URL 未配置")
        if not self.model:
            logger.warning("LLM_MODEL 未配置")

    def load_prompt(self) -> Optional[str]:
        try:
            if not os.path.exists(self.prompt_path):
                logger.error(f"Prompt 模板文件不存在: {self.prompt_path}")
                return None
            
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            logger.debug(f"成功加载 prompt 模板")
            return prompt_template
        except Exception as e:
            logger.error(f"加载 prompt 模板失败: {str(e)}")
            return None

    def build_prompt(self, variables: Dict[str, str]) -> Optional[str]:
        try:
            prompt_template = self.load_prompt()
            if not prompt_template:
                return None
            
            prompt = prompt_template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                prompt = prompt.replace(placeholder, str(value))
            
            logger.debug(f"成功构建 prompt")
            return prompt
        except Exception as e:
            logger.error(f"构建 prompt 失败: {str(e)}")
            return None

    def generate_alert(self, weather_variables: Dict[str, str]) -> Optional[str]:
        try:
            if not self.api_key or not self.base_url or not self.model:
                logger.error("LLM 配置不完整")
                return None
            
            prompt = self.build_prompt(weather_variables)
            if not prompt:
                logger.error("构建 prompt 失败")
                return None
            
            logger.info(f"调用 LLM 生成天气提醒，模型: {self.model}")
            
            # 使用 requests 直接调用 API，绕过 OpenAI SDK
            # 确保 API Key 是纯 ASCII，避免编码问题
            api_key_clean = str(self.api_key).strip()
            
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {api_key_clean}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # 确保 URL 正确
            api_url = self.base_url.rstrip('/') + '/chat/completions'
            
            # 清除所有代理环境变量，确保 requests 不用代理
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            os.environ.pop("http_proxy", None)
            os.environ.pop("https_proxy", None)
            
            # 使用会话，禁用代理
            session = requests.Session()
            session.trust_env = False  # 不使用系统环境的代理设置
            
            response = session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            alert_content = result["choices"][0]["message"]["content"].strip()
            logger.info(f"LLM 生成天气提醒成功")
            return alert_content
            
        except Exception as e:
            logger.error(f"生成天气提醒失败: {str(e)}", exc_info=True)
            return None
