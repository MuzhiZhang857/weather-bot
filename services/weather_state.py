"""
每个城市独立维护「告警事件去重 + 状态记忆」，并持久化到本地文件。

设计要点：
  * 以「规则标签 (tag)」作为告警的身份标识（指纹），而非当前时间或数值，
    从而满足：
      - 天气 API 轻微数值变化不会让 fingerprint 变化（同一 tag 只占一条状态）
      - 雨/雪事件直接复用预报驱动的稳定标签（如 "近期降水"），
        不需要拿当前时间做 fingerprint
  * 不使用全局冷却。每个城市、每个 tag 独立一条「活动态」记录。
  * 「活动态」去重：
      - 当某 tag 本次仍命中且已处于活动态 → 视为重复，不提醒
      - 当某 tag 首次命中（或之前解除）→ 记为新事件，提醒
      - 当某 tag 本次不再命中 → 自动解除活动态（resolved），
        未来再次命中即可再次提醒
  * 状态持久化：程序重启后已知活动态仍有效（不重复推送）。
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

CST = timezone(timedelta(hours=8))

# 事件型告警：通常来去匆匆、需要即时提醒且不常驻的连续状态
EVENT_TAG_PREFIXES = ("注意带伞", "注意防滑", "近期降水", "大风", "风寒明显")

# 状态型告警：较长时间维持、解除后仍会反复进入的状态
STATE_TAG_PREFIXES = ("高湿度", "高温", "低温", "酷热", "严寒", "昼夜温差大",
                      "强紫外线", "强UV", "感冒", "潮湿")


class WeatherState:
    """按城市隔离的告警活动态记忆，落盘到本地 JSON。"""

    def __init__(self, state_path: str = None, now=None):
        # 顶层: {city_id: {tag: {"time": iso, "type": "event"/"state"}}}
        self.state_path = state_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "state",
            "weather_state.json",
        )
        self._now = now or datetime.now(CST)
        self._data: Dict[str, Dict[str, dict]] = {}
        self._ensure_dir()
        self._load()

    # ------------------------------------------------------------------
    # 文件持久化
    # ------------------------------------------------------------------
    def _ensure_dir(self):
        d = os.path.dirname(self.state_path)
        if not os.path.exists(d):
            os.makedirs(d)

    def _load(self):
        if not os.path.exists(self.state_path):
            logger.info(f"状态文件不存在，从空状态开始: {self.state_path}")
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            # 规整为期望结构
            for city in self._data:
                self._data[city] = {t: {
                    "time": info.get("time", ""),
                    "type": info.get("type", "state"),
                } for t, info in self._data[city].items()}
            logger.info(f"已从 {self.state_path} 加载状态: {self._summarize()}")
        except Exception as e:
            logger.error(f"加载状态文件失败，从空状态开始: {str(e)}")
            self._data = {}

    def save(self):
        """原子写盘：先写临时文件再 rename，避免中途崩溃导致文件损坏。"""
        try:
            tmp = self.state_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.state_path)
            logger.debug(f"状态已保存到 {self.state_path}")
        except Exception as e:
            logger.error(f"保存状态文件失败: {str(e)}")

    def _summarize(self) -> str:
        return {c: list(tags) for c, tags in self._data.items()}

    # ------------------------------------------------------------------
    # 分类辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _tag_type(tag: str) -> str:
        for prefix in EVENT_TAG_PREFIXES:
            if tag.startswith(prefix):
                return "event"
        for prefix in STATE_TAG_PREFIXES:
            if tag.startswith(prefix):
                return "state"
        return "event"  # 默认按事件处理，倾向即时提醒

    # ------------------------------------------------------------------
    # 核心：去重 + 记忆
    # ------------------------------------------------------------------
    def get_new_tags(self, city_id: str, matched_tags: List[str]) -> List[str]:
        """返回本次命中、但尚未处于活动态的「新告警」标签列表。

        无论 matched_tags 是否为空都调用一次，内部会：
          * 把新命中的 tag 登记进活动态（首次 → 返回为新事件）
          * 把本次不再命中的 tag 从活动态移除（状态解除 → 未来可再次提醒）
        """
        city = self._data.setdefault(city_id, {})

        new_tags = []
        for tag in matched_tags:
            info = city.get(tag)
            if info is None:
                # 该 tag 尚未处于活动态 → 视为新告警（登记并持久化）
                city[tag] = self._make_entry(tag)
                new_tags.append(tag)
            else:
                logger.debug(
                    f"[{city_id}] tag '{tag}' 仍在活动态（{info.get('time')}），"
                    f"视为重复，不提醒"
                )
        self._prune(city_id, matched_tags)
        if new_tags:
            self.save()
        return new_tags

    def _make_entry(self, tag: str) -> dict:
        return {"time": self._now.isoformat(timespec="seconds"), "type": self._tag_type(tag)}

    def _prune(self, city_id: str, matched_tags: List[str]):
        """解除该城市本次未命中（不再匹配）的活动态。

        这是「告警解除后再次进入可再提醒」的关键：
        一个 tag 只要有一次不再命中，就立刻从活动态移除，
        未来它再次命中时会作为「新事件」再次输出。
        """
        city = self._data.get(city_id, {})
        matched_set: Set[str] = set(matched_tags)
        stale = [t for t in list(city.keys()) if t not in matched_set]
        for t in stale:
            city.pop(t, None)
            logger.info(f"[{city_id}] 告警解除，移除活动态: {t}")
        if stale:
            self.save()

    # ------------------------------------------------------------------
    # 测试实用
    # ------------------------------------------------------------------
    def is_active(self, city_id: str, tag: str) -> bool:
        return tag in self._data.get(city_id, {})

    def reset(self):
        self._data = {}