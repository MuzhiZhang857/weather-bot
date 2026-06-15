# Changelog

## [Unreleased]

### Fixed
- **时区修复**: 定时推送从 16:00 修正为 08:00。APScheduler `CronTrigger` 原本未指定 `timezone` 参数，在 UTC 服务器上被解释为 UTC 时间导致偏移 8 小时。现改用 `ZoneInfo("Asia/Shanghai")` 标准时区，确保按北京时间触发。

### Changed
- `services/scheduler.py`: `CST = timezone(timedelta(hours=8))` → `SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")`
- `BlockingScheduler()` → `BlockingScheduler(timezone=SHANGHAI_TZ)`
- `CronTrigger(hour=..., minute=...)` → `CronTrigger(hour=..., minute=..., timezone=SHANGHAI_TZ)`
- 变量名 `now_cst` → `now_shanghai`

---

## [0.1.0] - 2025-06-15

### Added
- 模块化 Service 层架构
- 和风天气 API 实时天气 + 7天预报 + 生活指数
- 语义规则引擎（湿度/温差/风力/降雨/降雪等标签）
- LLM 集成（通义千问/DeepSeek/智谱AI，OpenAI 兼容接口）
- 企业微信 WebSocket 消息推送
- APScheduler 定时调度
- Railway/Render 云部署支持
