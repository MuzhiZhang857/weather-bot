# BACKLOG — 暂不处理事项（ADP-1.0 §9）

> 职责：记录"现在不做，但以后可能做"的东西，并作为开发中非阻塞发现的唯一去处（ADP-1.0 §20）。
> **职责边界**：阻塞类用户决策（凭据处置、部署裁决等）在 `docs/STATE.md` §6，此处**不重复**；愿望型功能不进 ROADMAP。
> 规则：任何 Agent 不得因为本清单存在而顺手修改业务代码——每项都需独立 Task 与需求依据。

| ID | 标题 | 理由 | Priority | Source | Status |
|---|---|---|---|---|---|
| BL-001 | 修复或删除 `test_weather_service.py` | 第 10 行语法错误（STATE.md Bug B1）；verify.py 中按 KNOWN-BROKEN 标注。修复后还需处理其"直连真实 API"的测试方式 | High | STATE.md §4 B1 | Open |
| BL-002 | 移除或确认未使用依赖 `openai`、`schedule` | 全仓库无 import（TASK-000 审计核实）；删除前需按 ADP-1.0 §37 说明依据 | Medium | STATE.md §5（原 §5-2） | Open |
| BL-003 | 合并三处模板变量构建逻辑 | scheduler.py / main.py / weather_monitor.py 重复实现（含 time_of_day），改模板需同步三处，易漂移 | Medium | STATE.md §5（原 §5-3） | Open |
| BL-004 | 统一两套时区实现 | `ZoneInfo("Asia/Shanghai")`（scheduler）与固定 UTC+8（main/monitor/state）并存，当前等价但需单一事实 | Low | STATE.md §5（原 §5-4） | Open |
| BL-005 | 清理损坏的 `.venv`；评估 `.venv2` 无 pip 的补包方式 | `.venv` 指向已卸载解释器；`.venv2` 无法装新包 | Low | STATE.md §5（原 §5-5） | Open |
| BL-006 | 引入 lint / typecheck / CI（pytest 化测试） | 现无任何静态检查与 CI；手写脚本无断言（verify.py 已代断言语义输出） | Medium | STATE.md §5（原 §5-6） | Open |
| BL-007 | 修复 B2：JSON 规则只取第一个 condition key | 多条件规则被静默忽略；属语义引擎行为变更，需设计与回归 | Medium | STATE.md §4 B2 | Open |
| BL-008 | 修复 B3：SemanticEngine config 路径改为相对模块定位 | 相对 CWD 导致非项目根启动时规则静默丢失 | High | STATE.md §4 B3 | **Done (TASK-003)** |
| BL-009 | 修复 B4：`models/__init__.py` 补导出 `WeatherHourly` | 低风险一致性修复 | Low | STATE.md §4 B4 | Open |
| BL-010 | CHANGELOG 治理策略 | 停在 2025-06（STATE.md C6）；与 DEVELOPMENT_LOG 职责需划界（补记 or 归档声明） | Low | STATE.md §9 C6 | Open |
| BL-011 | `state/` 加入 `.gitignore` | 运行时状态不应入库 | Medium | STATE.md §5（原 §5-8） | **Done (TASK-003)** |
| BL-012 | 评估 push_service TLS 校验（`CERT_NONE`） | 已定级 **TRUE POSITIVE**（SEC-06）：MITM 可截获订阅载荷中的凭据并打通 response_url SSRF 链；修复设计 SEC-T3 已就绪（docs/SECURITY-REVIEW.md），恢复校验需 L3 实测授权 | High | STATE.md §5（原 §5-9）；TASK-004 | Open |
| BL-013 | 清理冗余模板变量 `current_time` | 代码构建但 prompt 未引用（ARCHITECTURE.md §8.2）；随 BL-003 一并处理 | Low | STATE.md §5（原 §5-10） | Open |
| BL-014 | README / WIKI 重写对齐当前形态 | C1（目录结构）、C2（规则数）、C3（运行模式）、C7（测试说明）——**应在 M2 定稿后做**，避免二次返工。⚠️ WIKI.md 含疑似真实凭证（STATE §6-1），**入库前必须先脱敏**（TASK-003 checkpoint 已将其排除在提交外） | Medium | STATE.md §9 | Open |
| BL-015 | watchdog 单元测试（weather_state 去重） | 已由 test_watchdog.py 22 例满足并入 verify.py 闭环 | High | TASK-000 迁移发现 | **Done (TASK-003)** |

> 新增条目规则：ID 递增（BL-020...），必须填全六列（ADP-1.0 §9）；完成后改 Status 并注明解决 Task。
| BL-016 | Hermes Integration Evidence（频率/stdout 消费/失败与并发语义） | REQ-013 端到端验证的前置；TASK-003 明确：M2 终验前解决，在此之前不得声称 Production/Hermes integration verified | High | TASK-003 任务书 Hermes Information 节 | Open |
| BL-017 | weather_monitor `setup_logging` 的 RotatingFileHandler 未显式 close（handlers.clear 时触发 ResourceWarning） | 无害（单次初始化 + GC 兜底），但测试输出有噪音；随日志层整理（BL-003/BL-006）一并处理 | Low | TASK-003 Gate Review（2026-09-30） | Open |
| BL-018 | **Mimosa L3 安全发现处置（独立安全任务）** — 分类：Historical security issue / **Not introduced by TASK-003** / Requires separate security task。清单：① `wechat_weather.py:4` legacy 硬编码凭据（与 STATE §6-1 同源，处置需先轮换）；② `wechat_weather.py:13/35/55/134` SSRF 启发式（URL 为硬编码常量，非外部可控——复核为误报，随 legacy 清理处理）；③ `main.py:110` response_url 使用平台回调 URL——**合理关切**，加固需 scheme/host 校验（行为变更，独立任务设计）；④ `weather_service.py:85` URL 拼接启发式（base_url/endpoint 均为内部常量——误报）；⑤ `weather_state.py:81` os.replace 路径启发式（路径来自模块定位或测试注入，无外部输入——误报）。**声明：TASK-003 checkpoint 经用户裁决（2026-09-30，方案 3）在上述发现存在下提交，不代表任何一项已解决；①③ 为真实安全工作项**。已由 TASK-004 定级：①→SEC-01 TP+历史、②→SEC-02 FP、③→SEC-03 TP、④→SEC-04 FP、⑤→SEC-05 FP（docs/SECURITY-REVIEW.md）。**U1 决议：仓库 Public（2026-09-30）→ 凭据暴露 CONFIRMED，轮换紧急度最高**。处置设计已产出（TASK-005）：docs/SECURITY-CREDENTIAL-REMEDIATION.md + 轮换执行计划（TASK-006）：docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md。**U5 决议 + TASK-007 Finalization：静态清理 ✅ + 平台失效 ✅（P1-P3）→ SEC-01/07/08 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN**——关键事实：SECRET/BOT_ID/CHAT_ID 泄露值=在用值（活凭据公开，已退役），HEFENG 泄露的是旧值（在用 key 未暴露） | High | Mimosa L3 pre-commit 扫描 + 用户裁决（2026-09-30） | Closed（凭据退役部分；SEC-T2→BL-019 / SEC-T3→BL-012 独立跟进） |
| BL-019 | response_url SSRF 加固（scheme/host 白名单 + 私有地址拒绝 + 禁重定向） | SEC-03 **TRUE POSITIVE**：外部影响 URL 直连 POST；修复设计 SEC-T2 已就绪（docs/SECURITY-REVIEW.md），实施需修改 main.py——待批准后独立立项 | High | TASK-004 | Open |
