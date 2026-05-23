# 智能天气提醒系统 - Product Requirement Document

## Overview

* **Summary**: 构建一个模块化、可扩展的智能天气提醒系统，集成企业微信推送、LLM 生成自然语言提醒、规则引擎语义分析

* **Purpose**: 解决天气信息推送的自动化和智能化问题，从简单天气数据推送升级为语义化、个性化的天气提醒

* **Target Users**: 企业用户通过企业微信群或个人账号接收智能天气提醒

## Goals

* 实现模块化的 Service 层架构

* 建立规则引擎解析天气语义

* 接入 LLM 生成自然语言天气提醒

* 使用 APScheduler 替代简单 while 循环

* 预留 Django 迁移能力和 AI Agent 扩展空间

* 支持通过 Railway Cron 触发任务

## Non-Goals (Out of Scope)

* 不开发前端页面

* 不做完整聊天机器人

* 不使用 LangChain 复杂封装

* 不构建多 Agent 系统

* 不开发无意义的 UI 代码

## Background & Context

* 现有代码已经具备：企业微信机器人推送、天气 API 获取、Railway 部署、GitHub 代码管理、基础文本推送

* 当前问题：时间戳显示 UTC 而非北京时间、架构不够模块化、缺少语义化和 LLM 能力

* 技术栈约束：Python 必须采用类型注解、环境变量配置、低耦合架构设计

## Functional Requirements

* **FR-1**: 天气服务模块独立获取、清洗天气数据并返回结构化数据

* **FR-2**: 语义引擎模块基于规则解析天气语义生成标签

* **FR-3**: LLM 服务模块调用 API 并从 prompt 模板生成自然语言提醒

* **FR-4**: 推送服务模块负责企业微信推送，具备重试和超时机制

* **FR-5**: 调度器模块使用 APScheduler 定时执行完整工作流

* **FR-6**: 支持完整工作流：获取天气 → 语义分析 → LLM 生成 → 推送消息

* **FR-7**: 所有配置使用 .env 文件，无硬编码

## Non-Functional Requirements

* **NFR-1**: 模块化架构，模块间低耦合

* **NFR-2**: 预留未来 Django 迁移能力

* **NFR-3**: 支持后续扩展 AI Agent 工作流

* **NFR-4**: 添加完善的日志记录

* **NFR-5**: 稳定运行在 Railway 环境中

## Constraints

* **Technical**: Python, 模块化设计, Service 层架构, APScheduler

* **Business**: 无特定业务约束

* **Dependencies**: 天气 API, LLM API (如 OpenAI 兼容 API), 企业微信机器人 API

## Assumptions

* 已有天气 API Key 和企业微信配置

* 可以使用任意 OpenAI 兼容的 LLM API

* Railway 环境变量可以完整配置

* 可部署到任何支持 Python 的云服务

## Acceptance Criteria

### AC-1: Weather Service 模块

* **Given**: 天气服务已配置 API Key

* **When**: 调用天气 API 获取指定城市天气

* **Then**: 返回清洗后的结构化天气数据，包含温度、湿度、风力、天气文本等字段

* **Verification**: `programmatic`

* **Notes**: 不包含提示词拼接、LLM 调用、消息推送逻辑

### AC-2: Semantic Engine 模块

* **Given**: 已获取结构化天气数据

* **When**: 应用语义规则进行解析

* **Then**: 返回包含天气标签的字典，如 {"weather\_tags": \["潮湿", "昼夜温差大"]}

* **Verification**: `programmatic`

* **Notes**: 不调用 LLM

### AC-3: LLM Service 模块

* **Given**: LLM API Key 已在 .env 中配置，有 prompt 模板文件

* **When**: 传入天气数据和语义标签调用 LLM 服务

* **Then**: 返回自然语言天气提醒，从 prompt 模板拼接

* **Verification**: `programmatic`

* **Notes**: 支持 prompt 文件化，无超长硬编码 prompt

### AC-4: Push Service 模块

* **Given**: 推送服务已配置企业微信 Bot ID 和 Secret

* **When**: 传入消息内容调用推送

* **Then**: 消息成功推送到企业微信，具备重试和超时机制，有日志记录

* **Verification**: `programmatic`

### AC-5: APScheduler 调度器

* **Given**: 配置了定时任务时间

* **When**: 调度器启动

* **Then**: 按设定时间执行完整工作流（天气获取 → 语义分析 → LLM → 推送），不使用 while True 循环

* **Verification**: `programmatic`

* **Notes**: 后续可迁移到 Railway Cron

### AC-6: 完整工作流集成

* **Given**: 所有模块已集成

* **When**: 工作流启动

* **Then**: 模块间松耦合，按顺序执行任务，日志完整输出

* **Verification**: `programmatic`

### AC-7: 目录结构和代码规范

* **Given**: 项目重构完成

* **When**: 检查目录结构和代码规范

* **Then**: 符合要求的 Service 层架构，使用类型注解，配置全部在 .env，可迁移到 Django

* **Verification**: `human-judgment`

## Open Questions

* [x] 具体使用哪个 LLM API? (主要使用国内 LLM：通义千问/DeepSeek/智谱AI)

* [x] 语义规则是否需要用户可配置？（支持一套预设配置，一套用户配置，支持可更改）

