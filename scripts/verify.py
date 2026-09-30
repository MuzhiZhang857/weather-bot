"""最小验证闭环：代码修改 → 编译检查 → 离线测试 → 验证报告。

用法（在项目根目录）：
    .venv2/Scripts/python.exe scripts/verify.py

只做三件事，全部离线、不发送任何消息、不调用外部 API：
  1. 编译检查：项目所有 .py 模块 py_compile（可发现语法级损坏，如 test_weather_service.py 的问题）；
  2. 离线语义测试：以子进程运行 test_semantic_engine.py，并对输出做轻量断言
     （该脚本本身无 assert，这里代为校验关键标签出现，防止规则引擎静默回归）；
  3. Watchdog 单元/流程测试：unittest 运行 test_watchdog.py（去重状态机、规则判定、
     城市解析、CWD 无关加载、stdout 契约与失败冻结——外部服务全部 mock）；
  4. 汇总 pass/fail，非零退出码表示失败（可直接用作 CI/pre-commit 钩子）。

注意：不覆盖 LLM/推送/天气 API 的真实路径——那些需要真实凭证并会外发消息，
手动验证方式见 docs/DEVELOPMENT.md §4 与 AGENTS.md §5。
"""
import py_compile
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 预期"场景名 → 至少应命中的标签"（与 test_semantic_engine.py 的用例一一对应）
EXPECTED_TAGS = {
    "潮湿测试": ["潮湿", "高湿度提醒"],
    "昼夜温差大测试": ["昼夜温差大"],
    "风寒明显测试": ["风寒明显"],
    "严寒测试": ["严寒", "低温预警"],
    "酷热测试": ["酷热", "高温预警"],
    "注意带伞测试": ["雨天预警"],
    "注意防滑测试": ["降雪预警"],
    "多重条件测试": ["大风预警", "潮湿", "降雪预警", "严寒"],
}

SKIP_DIRS = {
    ".venv", ".venv2", ".git", ".mimosa", ".trae", ".ai",
    "__pycache__", "logs", "state", "docs", "tasks", "scripts",
}

# 已知损坏、待用户决策（修复或删除）的文件：docs/STATE.md Bug B1。
# 这些文件编译失败计为 KNOWN-BROKEN（不阻塞整体结果）；一旦它们编译通过会提示从清单移除。
KNOWN_BROKEN = {
    "test_weather_service.py": "docs/STATE.md Bug B1",
}


def step_compile() -> bool:
    print("=" * 60)
    print("[1/2] 编译检查（py_compile 全项目 .py）")
    print("=" * 60)
    ok = True
    known_broken_left = []
    py_files = [
        p for p in sorted(PROJECT_ROOT.rglob("*.py"))
        if not (set(p.parts) & SKIP_DIRS)
    ]
    for py in py_files:
        rel = py.relative_to(PROJECT_ROOT)
        try:
            py_compile.compile(str(py), doraise=True)
            print(f"  OK    {rel}")
            if py.name in KNOWN_BROKEN:
                print(f"  NOTE  {rel} 已能编译？请同步修复 docs/STATE.md 并从 "
                      f"scripts/verify.py 的 KNOWN_BROKEN 移除")
        except py_compile.PyCompileError as e:
            if py.name in KNOWN_BROKEN:
                known_broken_left.append(py.name)
                ref = KNOWN_BROKEN[py.name]
                print(f"  KNOWN-BROKEN  {rel}  （预期内，见 {ref}）")
            else:
                ok = False
                first_line = str(e).strip().splitlines()[0]
                print(f"  FAIL  {rel}  {first_line}")
    print(f"编译检查：{'PASS' if ok else 'FAIL'}"
          f"（共 {len(py_files)} 个文件；已知损坏 {len(known_broken_left)} 个）")
    return ok


def step_semantic_tests() -> bool:
    print()
    print("=" * 60)
    print("[2/2] 离线语义引擎测试（test_semantic_engine.py）")
    print("=" * 60)
    proc = subprocess.run(
        [sys.executable, "test_semantic_engine.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if proc.returncode != 0:
        print(f"语义测试：FAIL（退出码 {proc.returncode}）")
        if proc.stderr:
            print(proc.stderr[-2000:])
        return False

    output = proc.stdout
    all_ok = True
    for scenario, tags in EXPECTED_TAGS.items():
        # 截取该场景的输出段
        start = output.find(scenario)
        if start == -1:
            print(f"{scenario}：FAIL（输出中找不到该场景）")
            all_ok = False
            continue
        end = output.find("测试场景", start + 1)
        segment = output[start:end if end != -1 else len(output)]
        missing = [t for t in tags if t not in segment]
        if missing:
            print(f"{scenario}：FAIL（缺少标签 {missing}）")
            all_ok = False
        else:
            print(f"{scenario}：PASS")

    if all_ok:
        print("语义测试：PASS（8 场景关键标签齐全）")
    else:
        print("语义测试：FAIL（存在场景断言不满足，规则引擎可能回归）")
    return all_ok


def step_watchdog_unittests() -> bool:
    print()
    print("=" * 60)
    print("[3/3] Watchdog 单元/流程测试（test_watchdog.py，全离线 mock）")
    print("=" * 60)
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "test_watchdog", "-v"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    for line in tail[-4:]:
        print(f"  {line}")
    if proc.returncode == 0:
        print("Watchdog 测试：PASS")
        return True
    print("Watchdog 测试：FAIL（详见上方输出）")
    return False


def main() -> int:
    print("weather-bot 最小验证闭环（离线，不发送任何消息）\n")
    results = {
        "compile": step_compile(),
        "semantic": step_semantic_tests(),
        "watchdog": step_watchdog_unittests(),
    }
    print()
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    for name, ok in results.items():
        print(f"  {name:<10} {'PASS' if ok else 'FAIL'}")
    if all(results.values()):
        print("\n全部通过。可以提交（提交规范见 docs/DEVELOPMENT.md §7）。")
        return 0
    print("\n存在失败项：修复后重跑，或在 docs/STATE.md 记录已知问题。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
