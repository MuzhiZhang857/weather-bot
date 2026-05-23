import os
import json
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from models.weather_types import WeatherData

logger = logging.getLogger(__name__)


@dataclass
class SemanticRule:
    rule_id: str
    tag: str
    condition: Dict[str, Any]
    enabled: bool = True


class SemanticEngine:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.default_rules_path = os.path.join(config_dir, "weather_rules_default.json")
        self.user_rules_path = os.path.join(config_dir, "weather_rules_user.json")
        self.rules: List[SemanticRule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        logger.info("开始加载语义规则")
        core_rules = self._get_core_rules()
        self.rules = core_rules
        self._load_rule_file(self.default_rules_path, is_default=True)
        self._load_rule_file(self.user_rules_path, is_default=False)
        logger.info(f"规则加载完成，共 {len(self.rules)} 条规则")

    def _get_core_rules(self) -> List[SemanticRule]:
        return [
            SemanticRule(
                rule_id="humidity_high",
                tag="潮湿",
                condition={"type": "humidity_above", "value": 85},
                enabled=True
            ),
            SemanticRule(
                rule_id="temp_diff_large",
                tag="昼夜温差大",
                condition={"type": "temp_diff_above", "value": 10},
                enabled=True
            ),
            SemanticRule(
                rule_id="wind_strong",
                tag="风寒明显",
                condition={"type": "wind_scale_above", "value": 5},
                enabled=True
            ),
            SemanticRule(
                rule_id="temp_freeze",
                tag="严寒",
                condition={"type": "temp_below", "value": 0},
                enabled=True
            ),
            SemanticRule(
                rule_id="temp_heat",
                tag="酷热",
                condition={"type": "temp_above", "value": 35},
                enabled=True
            ),
            SemanticRule(
                rule_id="rain_alert",
                tag="注意带伞",
                condition={"type": "weather_includes", "keywords": ["雨"]},
                enabled=True
            ),
            SemanticRule(
                rule_id="snow_alert",
                tag="注意防滑",
                condition={"type": "weather_includes", "keywords": ["雪"]},
                enabled=True
            )
        ]

    def _load_rule_file(self, file_path: str, is_default: bool) -> None:
        if not os.path.exists(file_path):
            logger.warning(f"规则文件不存在: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules_from_file = data.get('rules', [])
                logger.info(f"从 {'默认' if is_default else '用户'} 配置加载 {len(rules_from_file)} 条规则")
                
                for rule_data in rules_from_file:
                    rule_id = rule_data.get('rule_id', '')
                    tag = rule_data.get('name', '')
                    enabled = rule_data.get('enabled', True)
                    conditions = rule_data.get('conditions', {})
                    
                    if not rule_id or not tag:
                        continue
                    
                    condition_type = next(iter(conditions.keys()), None)
                    if condition_type:
                        value = conditions[condition_type]
                        condition = {"type": condition_type, "value": value}
                        
                        semantic_rule = SemanticRule(
                            rule_id=rule_id,
                            tag=tag,
                            condition=condition,
                            enabled=enabled
                        )
                        self.rules.append(semantic_rule)
                        logger.debug(f"添加规则: {rule_id} -> {tag}")
                        
        except Exception as e:
            logger.error(f"加载规则文件失败 {file_path}: {str(e)}")

    def _parse_numeric(self, value: Optional[str]) -> Optional[float]:
        if value is None or value == "N/A":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _extract_parameters(self, weather_data: WeatherData) -> Dict[str, Any]:
        params = {
            'temp': None,
            'temp_max': None,
            'temp_min': None,
            'humidity': None,
            'wind_scale': None,
            'weather_text': None,
            'weather_text_day': None,
            'uv_index': None,
            'cold_index': None
        }

        if weather_data.now:
            params['temp'] = self._parse_numeric(weather_data.now.temp)
            params['humidity'] = self._parse_numeric(weather_data.now.humidity)
            params['wind_scale'] = self._parse_numeric(weather_data.now.windScale)
            params['weather_text'] = weather_data.now.weather

        if weather_data.daily and weather_data.daily.daily_list:
            today = weather_data.daily.daily_list[0]
            params['temp_max'] = self._parse_numeric(today.tempMax)
            params['temp_min'] = self._parse_numeric(today.tempMin)
            params['weather_text_day'] = today.textDay

        if weather_data.indices:
            params['uv_index'] = weather_data.indices.uv
            params['cold_index'] = weather_data.indices.cold

        logger.debug(f"提取的天气参数: {params}")
        return params

    def _match_rule(self, rule: SemanticRule, params: Dict[str, Any]) -> bool:
        if not rule.enabled:
            return False

        condition = rule.condition
        condition_type = condition.get('type')

        if condition_type == 'humidity_above':
            threshold = condition.get('value')
            humidity = params.get('humidity')
            if humidity is not None and threshold is not None:
                result = humidity > threshold
                logger.debug(f"规则 {rule.rule_id}: 湿度 {humidity} > {threshold}? {result}")
                return result

        elif condition_type == 'temp_diff_above':
            threshold = condition.get('value')
            temp_max = params.get('temp_max')
            temp_min = params.get('temp_min')
            if temp_max is not None and temp_min is not None and threshold is not None:
                diff = abs(temp_max - temp_min)
                result = diff > threshold
                logger.debug(f"规则 {rule.rule_id}: 温差 {diff} > {threshold}? {result}")
                return result

        elif condition_type == 'wind_scale_above':
            threshold = condition.get('value')
            wind_scale = params.get('wind_scale')
            if wind_scale is not None and threshold is not None:
                result = wind_scale > threshold
                logger.debug(f"规则 {rule.rule_id}: 风力 {wind_scale} > {threshold}? {result}")
                return result

        elif condition_type == 'temp_below':
            threshold = condition.get('value')
            temp = params.get('temp')
            if temp is not None and threshold is not None:
                result = temp < threshold
                logger.debug(f"规则 {rule.rule_id}: 温度 {temp} < {threshold}? {result}")
                return result

        elif condition_type == 'temp_above':
            threshold = condition.get('value')
            temp = params.get('temp')
            if temp is not None and threshold is not None:
                result = temp > threshold
                logger.debug(f"规则 {rule.rule_id}: 温度 {temp} > {threshold}? {result}")
                return result

        elif condition_type == 'weather_includes':
            keywords = condition.get('value', [])
            if not isinstance(keywords, list):
                keywords = condition.get('keywords', [])
            weather_text = params.get('weather_text') or params.get('weather_text_day', '')
            if weather_text:
                for keyword in keywords:
                    if keyword in weather_text:
                        logger.debug(f"规则 {rule.rule_id}: 天气文本 '{weather_text}' 包含 '{keyword}'")
                        return True

        elif condition_type == 'uv_index_includes':
            keywords = condition.get('value', [])
            uv_index = params.get('uv_index', '')
            if uv_index:
                for keyword in keywords:
                    if keyword in uv_index:
                        logger.debug(f"规则 {rule.rule_id}: 紫外线指数 '{uv_index}' 包含 '{keyword}'")
                        return True

        elif condition_type == 'cold_index_includes':
            keywords = condition.get('value', [])
            cold_index = params.get('cold_index', '')
            if cold_index:
                for keyword in keywords:
                    if keyword in cold_index:
                        logger.debug(f"规则 {rule.rule_id}: 感冒指数 '{cold_index}' 包含 '{keyword}'")
                        return True

        return False

    def analyze(self, weather_data: WeatherData) -> Dict[str, List[str]]:
        logger.info("开始天气语义分析")
        
        params = self._extract_parameters(weather_data)
        matched_tags: Set[str] = set()

        for rule in self.rules:
            if self._match_rule(rule, params):
                matched_tags.add(rule.tag)
                logger.info(f"匹配规则: {rule.rule_id} → 标签: {rule.tag}")

        tags_list = list(matched_tags)
        logger.info(f"语义分析完成，匹配标签: {tags_list}")
        
        return {"weather_tags": tags_list}
