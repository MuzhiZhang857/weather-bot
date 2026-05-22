# 智能天气提醒系统 - Verification Checklist

## 基础架构验证
- [ ] 目录结构完整：services/, prompts/, models/, config/ 目录存在
- [ ] requirements.txt 包含所需依赖：python-dotenv, APScheduler, openai
- [ ] 类型注解正确应用在所有函数和类上
- [ ] 所有配置都从 .env 读取，无硬编码
- [ ] 模块间松耦合，可迁移到 Django

## Weather Service 验证
- [ ] weather_service.py 存在并可导入
- [ ] 成功调用天气 API 并返回清洗后的数据
- [ ] 返回数据结构符合类型定义
- [ ] 不包含提示词、LLM、推送逻辑

## Semantic Engine 验证
- [ ] semantic_engine.py 存在并可导入
- [ ] 湿度>85% 正确触发 "潮湿" 标签
- [ ] 温差>10℃ 正确触发 "昼夜温差大" 标签
- [ ] 风力>5级 正确触发 "风寒明显" 标签
- [ ] 返回格式符合 {"weather_tags": [...]} 要求
- [ ] 不调用 LLM

## LLM Service 验证
- [ ] llm_service.py 存在并可导入
- [ ] prompts/weather_alert.txt 模板存在
- [ ] 支持从环境变量读取 API Key
- [ ] 支持 prompt 模板加载和变量替换
- [ ] 正确调用 OpenAI 兼容 API
- [ ] 无硬编码超长 prompt 字符串

## Push Service 验证
- [ ] push_service.py 存在并可导入
- [ ] 支持企业微信消息推送
- [ ] 具备重试机制和超时机制
- [ ] 完整的日志记录
- [ ] 从环境变量读取配置

## Scheduler 验证
- [ ] scheduler.py 存在并可导入
- [ ] 使用 APScheduler，不使用 while True
- [ ] 支持定时任务调度
- [ ] 完整工作流按顺序执行：获取天气 → 语义分析 → LLM → 推送
- [ ] 支持后续 Railway Cron 迁移

## 集成验证
- [ ] main.py 存在并可正常运行
- [ ] 所有服务模块正确集成
- [ ] 日志输出完整
- [ ] 支持直接运行和定时运行两种模式
