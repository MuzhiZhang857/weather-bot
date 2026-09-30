"""Watchdog 正确性测试（TASK-003 / D2，全离线，不发送任何真实消息）。

运行方式（项目根）：
    .venv2/Scripts/python.exe -m unittest test_watchdog -v

覆盖：
  - WeatherState 去重状态机：新事件 → 去重 → 解除 → 再告警；持久化/恢复/损坏容错；多城市隔离；原子写无残留
  - SemanticEngine 规则：precip_soon_in 三信号（文本/pop/precip）与窗口边界；D1 修复后任意 CWD 规则完整加载
  - 城市解析：CITY_SLUGS / CITY_NAMES / CITY_ID 回退全形式
  - monitor 流程级离线集成：stdout 契约（新告警输出、未命中/重复零输出）与取数失败冻结状态
    （天气/LLM 外部服务以 mock 替换——L2 offline integration 级别）

注意：所有涉及状态的测试一律注入临时目录路径，绝不触碰 state/weather_state.json 真实运行数据。
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from models.weather_types import (
    DailyWeather,
    IndicesData,
    Weather7D,
    WeatherData,
    WeatherHourly,
    WeatherNow,
)
from services.semantic_engine import SemanticEngine
from services.weather_state import WeatherState

PROJECT_ROOT = Path(__file__).resolve().parent
CITY_A = {"id": "101080201", "name": "城市甲"}
CITY_B = {"id": "101080101", "name": "城市乙"}

COLD_TAGS = ["严寒", "低温预警"]


def _cold_weather(city_name):
    """确定性命中 严寒+低温预警 的天气数据（温差=10 不触发温差规则，其余中性）。"""
    return WeatherData(
        city_name=city_name,
        city_id="",
        now=WeatherNow(temp="-5", feelsLike="-8", weather="晴", windDir="北",
                       windScale="2", humidity="40"),
        daily=Weather7D(daily_list=[DailyWeather(textDay="晴", tempMax="0", tempMin="-10")]),
        hourly=[],
        indices=IndicesData(),
    )


def _neutral_weather(city_name):
    """不命中任何规则的天气数据。"""
    return WeatherData(
        city_name=city_name,
        city_id="",
        now=WeatherNow(temp="20", feelsLike="20", weather="晴", windDir="南",
                       windScale="2", humidity="50"),
        daily=Weather7D(daily_list=[DailyWeather(textDay="晴", tempMax="25", tempMin="15")]),
        hourly=[],
        indices=IndicesData(),
    )


def _hourly(text="阴", pop="0", precip="0.0"):
    return WeatherHourly(fxTime="t", text=text, temp="20", pop=pop, precip=precip)


class WeatherStateTests(unittest.TestCase):
    """AC-2 / AC-3：去重状态机与持久化。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_path = str(Path(self._tmp.name) / "weather_state.json")

    def _state(self):
        return WeatherState(state_path=self.state_path)

    def test_first_hit_is_new_event_and_persisted(self):
        state = self._state()
        self.assertEqual(state.get_new_tags("c1", ["低温预警"]), ["低温预警"])
        self.assertTrue(state.is_active("c1", "低温预警"))
        data = json.loads(Path(self.state_path).read_text(encoding="utf-8"))
        self.assertIn("低温预警", data["c1"])
        self.assertIn("time", data["c1"]["低温预警"])
        self.assertIn("type", data["c1"]["低温预警"])

    def test_duplicate_suppressed(self):
        state = self._state()
        state.get_new_tags("c1", ["低温预警"])
        self.assertEqual(state.get_new_tags("c1", ["低温预警"]), [])

    def test_release_then_realert(self):
        state = self._state()
        state.get_new_tags("c1", ["低温预警"])
        state.get_new_tags("c1", [])                      # 条件消失 → 解除
        self.assertFalse(state.is_active("c1", "低温预警"))
        self.assertEqual(state.get_new_tags("c1", ["低温预警"]), ["低温预警"])  # 再现 → 再告警

    def test_multi_tag_mixed_new_and_duplicate(self):
        state = self._state()
        state.get_new_tags("c1", ["严寒"])
        self.assertEqual(sorted(state.get_new_tags("c1", ["严寒", "低温预警"])), ["低温预警"])

    def test_persistence_roundtrip(self):
        state = self._state()
        state.get_new_tags("c1", ["低温预警"])
        state.get_new_tags("c2", ["大风预警"])
        reloaded = self._state()
        self.assertTrue(reloaded.is_active("c1", "低温预警"))
        self.assertTrue(reloaded.is_active("c2", "大风预警"))
        self.assertFalse(reloaded.is_active("c1", "严寒"))

    def test_corrupted_json_starts_empty(self):
        # 真实损坏场景（DESIGN §5.3 失败边界）：文件可正常打开、内容为非法 JSON
        # （静态 fixture 模拟写入中途崩溃产生的截断文件），json 解码失败 → 从空状态开始
        fixture = Path(PROJECT_ROOT) / "tests" / "fixtures" / "corrupted_weather_state.json"
        self.assertNotEqual(fixture.stat().st_size, 0)      # fixture 本身存在且有内容
        Path(self.state_path).write_text(
            fixture.read_text(encoding="utf-8"), encoding="utf-8")
        state = self._state()
        self.assertEqual(state.get_new_tags("c1", ["低温预警"]), ["低温预警"])  # 按新告警重建
        # 自愈：损坏被合法状态覆盖后，重新加载语义正常
        reloaded = self._state()
        self.assertTrue(reloaded.is_active("c1", "低温预警"))

    def test_unreadable_state_file_starts_empty(self):
        # 另一故障模式：路径存在但不可作为文件读取（如目录占位）——与内容损坏不同的失败路径
        os.mkdir(self.state_path)
        state = self._state()
        self.assertEqual(state.get_new_tags("c1", ["低温预警"]), ["低温预警"])

    def test_multi_city_isolation(self):
        state = self._state()
        state.get_new_tags("c1", ["低温预警"])
        self.assertEqual(state.get_new_tags("c2", ["低温预警"]), ["低温预警"])

    def test_atomic_save_leaves_no_tmp(self):
        state = self._state()
        state.get_new_tags("c1", ["低温预警"])
        leftovers = [f for f in os.listdir(self._tmp.name) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])


class ConfigResolutionTests(unittest.TestCase):
    """AC-6（D1 修复）与 AC-4：规则加载不依赖 CWD；显式 config_dir 覆盖语义不变。"""

    def test_rules_load_regardless_of_cwd(self):
        # 在项目根之外的干净子进程中启动，验证规则仍完整加载（AC-6）
        snippet = (
            "import json;"
            "from services.semantic_engine import SemanticEngine;"
            "print(json.dumps([r.rule_id for r in SemanticEngine().rules]))"
        )
        proc = subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=tempfile.gettempdir(),
            env=dict(os.environ, PYTHONPATH=str(PROJECT_ROOT)),
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rule_ids = json.loads(proc.stdout.strip())
        self.assertIn("temp_freeze", rule_ids)        # 核心规则
        self.assertIn("precip_soon_alert", rule_ids)  # 默认 JSON 规则
        self.assertIn("custom_example", rule_ids)     # 用户 JSON 规则

    def test_explicit_config_dir_override(self):
        # 显式 config_dir 时尊重传入值：目录内无 JSON → 仅剩 7 条核心规则
        with tempfile.TemporaryDirectory() as config_dir:
            engine = SemanticEngine(config_dir=config_dir)
            rule_ids = [rule.rule_id for rule in engine.rules]
        self.assertEqual(len(rule_ids), 7)
        self.assertIn("temp_freeze", rule_ids)
        self.assertNotIn("precip_soon_alert", rule_ids)

    def test_city_parsing_forms(self):
        from services.weather_service import WeatherService

        def cities(**env):
            with mock.patch.dict(os.environ, env):
                return WeatherService().get_cities()

        # 仅 CITY_SLUGS（slug=ID）
        self.assertEqual(
            cities(CITY_SLUGS="baotou=101080201", CITY_NAMES="", CITY_ID=""),
            [{"id": "101080201", "name": "baotou"}])
        # CITY_SLUGS + CITY_NAMES 映射
        self.assertEqual(
            cities(CITY_SLUGS="baotou=101080201", CITY_NAMES="baotou=包头", CITY_ID=""),
            [{"id": "101080201", "name": "包头"}])
        # 回退单城市 CITY_ID
        self.assertEqual(
            cities(CITY_SLUGS="", CITY_NAMES="", CITY_ID="101080101", CITY_NAME="呼和浩特"),
            [{"id": "101080101", "name": "呼和浩特"}])
        # 两者皆无 → 空列表
        self.assertEqual(
            cities(CITY_SLUGS="", CITY_NAMES="", CITY_ID=""), [])


class PrecipSoonRuleTests(unittest.TestCase):
    """AC-1：precip_soon_in 三信号与窗口边界。"""

    def setUp(self):
        self.engine = SemanticEngine()

    def _tags(self, hourly):
        data = WeatherData(
            city_name="测试城",
            now=WeatherNow(temp="20", weather="晴", windScale="2", humidity="50"),
            daily=Weather7D(daily_list=[DailyWeather(textDay="晴", tempMax="25", tempMin="15")]),
            hourly=hourly,
            indices=IndicesData(),
        )
        return self.engine.analyze(data)["weather_tags"]

    def test_text_signal_hit(self):
        self.assertIn("近期降水提醒", self._tags([_hourly(text="小雨")]))

    def test_pop_signal_hit(self):
        self.assertIn("近期降水提醒", self._tags([_hourly(text="阴", pop="45")]))

    def test_precip_signal_hit(self):
        self.assertIn("近期降水提醒", self._tags([_hourly(text="阴", precip="1.2")]))

    def test_outside_window_no_hit(self):
        clear = [_hourly() for _ in range(3)]
        late_rain = _hourly(text="小雨")
        self.assertNotIn("近期降水提醒", self._tags(clear + [late_rain]))

    def test_all_clear_no_hit(self):
        self.assertNotIn("近期降水提醒", self._tags([_hourly() for _ in range(5)]))

    def test_alert_lead_hours_override(self):
        from weather_monitor import apply_lead_hours
        engine = SemanticEngine()
        apply_lead_hours(engine, 5)  # 提前量改 5 小时
        clear4 = [_hourly() for _ in range(4)]
        late_rain = _hourly(text="小雨")
        data = WeatherData(
            city_name="测试城",
            now=WeatherNow(temp="20", weather="晴", windScale="2", humidity="50"),
            daily=Weather7D(daily_list=[DailyWeather(textDay="晴", tempMax="25", tempMin="15")]),
            hourly=clear4 + [late_rain],
            indices=IndicesData(),
        )
        self.assertIn("近期降水提醒", engine.analyze(data)["weather_tags"])


class MonitorFlowTests(unittest.TestCase):
    """AC-5 + 取数失败冻结状态：流程级离线集成（mock 天气/LLM，真实规则与状态机）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_path = str(Path(self._tmp.name) / "weather_state.json")

    def _run_monitor(self, cities, weather_results):
        """以 mock 外部服务运行 weather_monitor.main()，返回 stdout 内容。"""
        import services.llm_service as llm_module
        import services.weather_service as ws_module
        import services.weather_state as state_module
        import weather_monitor

        real_state_cls = WeatherState

        def fake_state():
            return real_state_cls(state_path=self.state_path)

        stdout = io.StringIO()
        with mock.patch("sys.argv", ["weather_monitor.py"]), \
             mock.patch.object(ws_module.WeatherService, "get_cities",
                               return_value=cities), \
             mock.patch.object(ws_module.WeatherService, "get_complete_weather",
                               side_effect=weather_results), \
             mock.patch.object(llm_module.LLMService, "generate_alert",
                               lambda self, variables: f"提醒：{variables['city_name']}"), \
             mock.patch.object(state_module, "WeatherState", fake_state), \
             redirect_stdout(stdout):
            weather_monitor.main()
        return stdout.getvalue()

    def test_new_alert_printed_to_stdout(self):
        out = self._run_monitor([CITY_A], [_cold_weather("城市甲")])
        self.assertEqual(out.strip(), "提醒：城市甲")

    def test_duplicate_alert_suppressed(self):
        WeatherState(state_path=self.state_path).get_new_tags(CITY_A["id"], COLD_TAGS)
        out = self._run_monitor([CITY_A], [_cold_weather("城市甲")])
        self.assertEqual(out, "")

    def test_no_hit_silent(self):
        out = self._run_monitor([CITY_A], [_neutral_weather("城市甲")])
        self.assertEqual(out, "")

    def test_fetch_failure_freezes_state(self):
        WeatherState(state_path=self.state_path).get_new_tags(CITY_A["id"], COLD_TAGS)
        out = self._run_monitor([CITY_A], [None])  # 取数失败
        self.assertEqual(out, "")                  # 不输出
        state = WeatherState(state_path=self.state_path)
        self.assertTrue(state.is_active(CITY_A["id"], "严寒"))       # 状态冻结
        self.assertTrue(state.is_active(CITY_A["id"], "低温预警"))   # 不因失败误解除

    def test_two_cities_partial_failure(self):
        out = self._run_monitor([CITY_A, CITY_B], [None, _cold_weather("城市乙")])
        self.assertIn("提醒：城市乙", out)
        self.assertNotIn("城市甲", out)            # 失败城市无输出
        state = WeatherState(state_path=self.state_path)
        self.assertFalse(state._data.get(CITY_A["id"]))              # 甲状态未被触碰
        self.assertTrue(state.is_active(CITY_B["id"], "严寒"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
