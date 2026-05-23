import os
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
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

    def generate_simple_alert(self, variables: Dict[str, str]) -> str:
        """使用简单模板生成天气提醒（降级方案）"""
        try:
            template = f"""{variables.get('city_name', '未知城市')}天气预报

🌡 今日实况：
• 天气：{variables.get('weather', '未知')}
• 温度：{variables.get('temp', 'N/A')}°C（体感 {variables.get('feels_like', 'N/A')}°C）
• 湿度：{variables.get('humidity', 'N/A')}%
• 风力：{variables.get('wind_dir', 'N/A')} {variables.get('wind_scale', 'N/A')}级

📅 明日预告：
• 天气：{variables.get('tomorrow_weather', '未知')}
• 温度：{variables.get('tomorrow_temp_min', 'N/A')}~{variables.get('tomorrow_temp_max', 'N/A')}°C

【生活指数】
• 穿衣：{variables.get('dressing_index', 'N/A')}
• 紫外线：{variables.get('uv_index', 'N/A')}
• 舒适度：{variables.get('comfort_index', 'N/A')}

✨ {variables.get('alert_tags', '无特殊提醒')}"""

            logger.info("使用降级方案生成简单天气提醒")
            return template
        except Exception as e:
            logger.error(f"生成简单天气提醒失败: {str(e)}")
            return f"{variables.get('city_name', '天气')}提醒：获取天气信息完成。"

    def _create_session_with_retry(self) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def generate_alert(self, weather_variables: Dict[str, str]) -> Optional[str]:
        """尝试使用 LLM 生成天气提醒，失败时使用简单模板"""
        try:
            if not self.api_key or not self.base_url or not self.model:
                logger.error("LLM 配置不完整，使用降级方案")
                return self.generate_simple_alert(weather_variables)
            
            prompt = self.build_prompt(weather_variables)
            if not prompt:
                logger.error("构建 prompt 失败，使用降级方案")
                return self.generate_simple_alert(weather_variables)
            
            logger.info(f"调用 LLM 生成天气提醒，模型: {self.model}，超时: {self.timeout}秒")
            
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
            
            api_url = self.base_url.rstrip('/') + '/chat/completions'
            
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            os.environ.pop("http_proxy", None)
            os.environ.pop("https_proxy", None)
            
            session = self._create_session_with_retry()
            session.trust_env = False
            
            response = session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            alert_content = result["choices"][0]["message"]["content"].strip()
            logger.info(f"LLM 生成天气提醒成功")
            return alert_content
            
        except requests.exceptions.Timeout as e:
            logger.error(f"LLM API 调用超时（{self.timeout}秒），使用降级方案: {str(e)}")
            return self.generate_simple_alert(weather_variables)
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败，使用降级方案: {str(e)}")
            return self.generate_simple_alert(weather_variables)
        except Exception as e:
            logger.error(f"生成天气提醒失败，使用降级方案: {str(e)}", exc_info=True)
            return self.generate_simple_alert(weather_variables)
