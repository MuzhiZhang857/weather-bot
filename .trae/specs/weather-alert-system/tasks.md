# 智能天气提醒系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 创建项目目录结构和配置文件
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建标准 Service 层目录结构：`services/`, `prompts/`, `config/`
  - 更新 `requirements.txt` 新增依赖：`python-dotenv`, `APScheduler`, `openai`
  - 更新 `.env.example` 新增配置项
  - 创建 `README.md` 更新项目说明
  - 创建类型定义文件 `models/weather_types.py`
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-1.1: 检查目录结构是否完整
  - `human-judgment` TR-1.2: 检查 requirements.txt 是否包含所有依赖
- **Notes**: 后续可迁移到 Django，确保目录结构具备可扩展性

## [ ] Task 2: 实现 weather_service.py
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 创建 `services/weather_service.py`
  - 实现天气 API 请求和数据清洗
  - 返回结构化的天气数据（使用类型注解）
  - 不包含提示词、LLM 调用、消息推送逻辑
- **Acceptance Criteria Addressed**: [AC-1, AC-7]
- **Test Requirements**:
  - `programmatic` TR-2.1: 调用 API 并验证返回数据结构
  - `programmatic` TR-2.2: 验证数据清洗逻辑

## [ ] Task 3: 实现 semantic_engine.py
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 创建 `services/semantic_engine.py`
  - 实现规则引擎解析天气语义
  - 支持：湿度 > 85% → "潮湿"，温差 > 10℃ → "昼夜温差大"，风力 > 5级 → "风寒明显" 等规则
  - 返回 `{"weather_tags": [...]}` 结构
  - 不调用 LLM
- **Acceptance Criteria Addressed**: [AC-2, AC-7]
- **Test Requirements**:
  - `programmatic` TR-3.1: 测试各项语义规则是否正确触发
  - `programmatic` TR-3.2: 验证返回数据格式

## [ ] Task 4: 实现 llm_service.py 和 prompt 模板
- **Priority**: P0
- **Depends On**: Task 3
- **Description**:
  - 创建 `services/llm_service.py`
  - 创建 `prompts/weather_alert.txt` 模板文件
  - 实现 LLM API 调用（兼容 OpenAI 格式）
  - 从环境变量读取 API Key 和配置
  - 支持 prompt 模板加载和上下文拼接
- **Acceptance Criteria Addressed**: [AC-3, AC-7]
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证 prompt 模板正确加载和变量替换
  - `programmatic` TR-4.2: 验证 LLM 调用和返回结果

## [ ] Task 5: 实现 push_service.py
- **Priority**: P0
- **Depends On**: Task 4
- **Description**:
  - 创建 `services/push_service.py`
  - 实现企业微信机器人推送
  - 添加 retry 机制和 timeout 机制
  - 添加完整的日志记录
  - 从环境变量读取配置
- **Acceptance Criteria Addressed**: [AC-4, AC-7]
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证消息推送成功
  - `programmatic` TR-5.2: 验证重试机制在失败情况下工作

## [ ] Task 6: 实现 scheduler.py (APScheduler)
- **Priority**: P0
- **Depends On**: Task 5
- **Description**:
  - 创建 `services/scheduler.py`
  - 使用 APScheduler 替代 while True
  - 支持完整工作流调度：获取天气 → 语义分析 → LLM生成 → 推送
  - 支持后续 Railway Cron 迁移
  - 不使用 while True 循环
- **Acceptance Criteria Addressed**: [AC-5, AC-7]
- **Test Requirements**:
  - `programmatic` TR-6.1: 验证 APScheduler 正确注册任务
  - `programmatic` TR-6.2: 验证完整工作流调用顺序

## [ ] Task 7: 创建 main.py 入口文件和日志配置
- **Priority**: P0
- **Depends On**: Task 6
- **Description**:
  - 创建 `main.py` 入口文件
  - 整合所有服务模块
  - 配置日志系统
  - 支持直接运行和定时启动两种模式
- **Acceptance Criteria Addressed**: [AC-6, AC-7]
- **Test Requirements**:
  - `human-judgment` TR-7.1: 验证模块间低耦合
  - `programmatic` TR-7.2: 验证完整工作流正常执行
  - `human-judgment` TR-7.3: 检查日志输出完整

## [ ] Task 8: 更新项目配置文件
- **Priority**: P1
- **Depends On**: Task 1
- **Description**:
  - 更新 `railway.json` 和 `render.yaml`
  - 更新 `requirements.txt` 新依赖
  - 更新 `.gitignore`
  - 更新 README 文档
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `human-judgment` TR-8.1: 验证配置文件完整
