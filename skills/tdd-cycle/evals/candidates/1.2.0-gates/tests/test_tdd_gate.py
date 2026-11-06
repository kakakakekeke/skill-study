"""tdd_gate.py·red_check.py 단위 테스트. 훅을 Claude Code가 주는 stdin JSON 형식으로 구동한다.
실행: python3 -m pytest skills/tdd-cycle/evals/candidates/1.2.0-gates/tests -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# 후보 1.2.0 디렉터리(evals/candidates/1.2.0-gates) 안의 훅·스크립트를 검사한다
SKILL = Path(__file__).resolve().parents[1]
GATE = SKILL / "hooks" / "tdd_gate.py"
RED_CHECK = SKILL / "scripts" / "red_check.py"
sys.path.insert(0, str(SKILL / "scripts"))
import tdd_state  # noqa: E402


@pytest.fixture
def proj(tmp_path, monkeypatch):
    """git 없는 임시 프로젝트. TDD_MODE=1, 상태 파일은 tmp 아래."""
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "__init__.py").write_text("")
    state_dir = tmp_path / "state"
    env = {**os.environ, "TDD_MODE": "1", "TDD_CYCLE_STATE_DIR": str(state_dir), "PYTHONDONTWRITEBYTECODE": "1"}
    monkeypatch.setenv("TDD_CYCLE_STATE_DIR", str(state_dir))
    tdd_state.STATE_DIR = state_dir

    class P:
        def __init__(self):
            self.root, self.env, self.sid = root, env, "s1"

        def hook(self, event: str, **kw) -> dict | None:
            data = {"hook_event_name": event, "session_id": self.sid, "cwd": str(root), **kw}
            r = subprocess.run([sys.executable, str(GATE)], input=json.dumps(data), capture_output=True, text=True,
                               env=env, cwd=root, timeout=30)
            assert r.returncode == 0, r.stderr
            assert "tdd_gate:" not in r.stderr, r.stderr  # 훅 내부 예외는 실패로 본다
            return json.loads(r.stdout) if r.stdout.strip() else None

        def pre(self, tool: str, **inp):
            return self.hook("PreToolUse", tool_name=tool, tool_input=inp)

        def decision(self, tool: str, **inp) -> tuple[str, str]:
            r = self.pre(tool, **inp)
            if r is None:
                return "allow", ""
            h = r["hookSpecificOutput"]
            return h.get("permissionDecision", "allow"), h.get("permissionDecisionReason", "")

        def write(self, rel: str, content: str) -> tuple[str, str]:
            """Write 도구를 훅에 통과시키고, 허용되면 실제로 쓴다."""
            d, why = self.decision("Write", file_path=str(root / rel), content=content)
            if d == "allow":
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(content)
            return d, why

        def post_bash(self, command: str, stdout: str):
            return self.hook("PostToolUse", tool_name="Bash", tool_input={"command": command},
                             tool_response={"stdout": stdout, "stderr": ""})

        def red_check(self, *args) -> tuple[int, str]:
            r = subprocess.run([sys.executable, str(RED_CHECK), *args], capture_output=True, text=True, env=env, cwd=root, timeout=120)
            return r.returncode, r.stdout + r.stderr

        def state(self) -> dict:
            return tdd_state.load(root)

    p = P()
    p.hook("UserPromptSubmit", prompt="README대로 구현해줘")
    return p


def test_mode_on_by_env_injects_context(proj):
    r = proj.hook("UserPromptSubmit", prompt="구현해줘")
    assert "TDD 모드" in r["hookSpecificOutput"]["additionalContext"]


# ---- 1단계: 결과를 못 읽은 pytest → unknown ----------------------------------------

def test_unreadable_pytest_output_blocks_until_rerun(proj):
    proj.write("tests/test_a.py", "from m import f\ndef test_a():\n    assert f() == 1\n")
    proj.write("m.py", "def f():\n    pass\n")  # red_missing 아님: none 상태라 거부되지만 파일은 직접 둔다
    (proj.root / "m.py").write_text("def f():\n    pass\n")
    code, _ = proj.red_check("tests/test_a.py")
    assert code == 0  # RED (동작)
    assert proj.state()["state"] == "red"
    # 모델이 출력을 잘라서 돌림: 요약 줄이 없다
    r = proj.post_bash("python -m pytest tests/test_a.py -q 2>&1 | tail -1", "assert None == 1")
    assert proj.state()["state"] == "unknown"
    assert "읽지 못했다" in r["hookSpecificOutput"]["additionalContext"]
    d, why = proj.write("m.py", "def f():\n    return 1\n")
    assert d == "deny" and "읽지 못했다" in why
    code, _ = proj.red_check("tests/test_a.py")
    assert code == 0 and proj.state()["state"] == "red"
    d, _ = proj.write("m.py", "def f():\n    return 1\n")
    assert d == "allow"


@pytest.mark.parametrize("cmd,expected", [
    ("python -m pytest tests -q", True),
    ("pytest tests/test_a.py::test_a -x", True),
    ("cd proj && pytest", True),
    ("pytest --version", False),
    ("pip install pytest", False),
    ("cat > tests/test_a.py <<'EOF'\nimport pytest\n\ndef test_a():\n    pass\nEOF", False),
    ("cat > tests/test_a.py <<'EOF'\nimport pytest\nEOF\npytest tests/test_a.py", True),
    ("pytest --collect-only -q", False),
    ("echo pytest", False),
    ("grep -n pytest pyproject.toml", False),
    ("PYTHONPATH=. pytest tests -q", True),
    ("uv run pytest tests", True),
    ("timeout 60 pytest tests", True),
    ("pytest tests -q 2>&1 | tail -3", True),
])
def test_runs_pytest_detection(cmd, expected):
    assert tdd_state.runs_pytest(cmd) is expected


def test_pytest_mention_in_heredoc_does_not_change_state(proj):
    proj.post_bash("cat > tests/test_b.py <<'EOF'\nimport pytest\n\ndef test_b():\n    assert 1\nEOF", "")
    assert proj.state()["state"] == "none"
    proj.post_bash("grep -n pytest pyproject.toml", "[tool.pytest.ini_options]")
    assert proj.state()["state"] == "none"


def test_no_tests_ran_is_not_unknown(proj):
    proj.post_bash("pytest -q", "no tests ran in 0.01s")
    assert proj.state()["state"] == "none"


def test_growth_count_ignores_comment_lines():
    assert tdd_state.nonblank("# a\n\nx = 1\n  # b\ny = 2\n") == 2


def test_unusual_invocation_with_readable_output_still_applies(proj):
    """명령 위치 판정이 놓친 호출이라도(1.1.0과 같이) 결과가 읽히면 반영한다."""
    proj.post_bash("./run_tests.sh --runner pytest", "FAILED tests/test_a.py::test_a - assert None == 1\n1 failed in 0.1s")
    assert proj.state()["state"] == "red"


# ---- 2단계 (a): 이 세션에서 쓴 테스트가 RED 없이 통과 → --ack 전까지 차단 -----------------

def _green_cycle(proj):
    """테스트 하나 → RED → 최소 구현 → GREEN. 상태 green으로 끝난다."""
    proj.write("tests/test_a.py", "from m import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    (proj.root / "m.py").write_text("def add(a, b):\n    pass\n")
    assert proj.red_check("tests/test_a.py")[0] == 0
    assert proj.write("m.py", "def add(a, b):\n    return a + b\n")[0] == "allow"
    assert proj.red_check()[0] == 1


def test_no_red_test_written_here_blocks_until_ack(proj):
    _green_cycle(proj)
    # 새 테스트가 처음부터 통과한다(앞 사이클 구현이 미리 넣은 동작)
    proj.write("tests/test_b.py", "from m import add\ndef test_add_zero():\n    assert add(0, 0) == 0\n")
    code, outp = proj.red_check("tests/test_b.py")
    assert code == 1 and "RED 없음" in outp and "--ack" in outp
    assert proj.state()["no_red_pending"] == ["test_add_zero"]
    # 다음 테스트로 RED를 만들어도 소스 수정은 ack 전까지 막힌다
    proj.write("tests/test_c.py", "from m import add\ndef test_add_neg():\n    assert add(-1, 1) == 'zero'\n")
    assert proj.red_check("tests/test_c.py")[0] == 0
    d, why = proj.write("m.py", "def add(a, b):\n    return 'zero' if a + b == 0 else a + b\n")
    assert d == "deny" and "RED 없음" in why and "--ack test_add_zero" in why
    code, outp = proj.red_check("--ack", "test_wrong_name")
    assert code == 3
    code, outp = proj.red_check("--ack", "test_add_zero")
    assert code == 0 and proj.state()["no_red_pending"] == [] and proj.state()["acks"] == 1
    assert proj.write("m.py", "def add(a, b):\n    return 'zero' if a + b == 0 else a + b\n")[0] == "allow"


def test_no_red_clears_when_expectation_fixed_to_red(proj):
    _green_cycle(proj)
    proj.write("tests/test_b.py", "from m import add\ndef test_add_zero():\n    assert add(0, 0) == 0\n")
    proj.red_check("tests/test_b.py")
    assert proj.state()["no_red_pending"] == ["test_add_zero"]
    # 기대값을 고쳐 동작 RED를 본다 → 자동 해제
    proj.write("tests/test_b.py", "from m import add\ndef test_add_zero():\n    assert add(0, 0) == 'zero'\n")
    assert proj.red_check("tests/test_b.py")[0] == 0
    assert proj.state()["no_red_pending"] == []


def test_preexisting_test_first_run_later_is_not_gated(proj):
    """세션 전에 있던 테스트 파일을 나중에 처음 돌려도(기존 테스트) 게이트에 걸리지 않는다. 메모만 남는다."""
    (proj.root / "tests" / "test_old.py").write_text("def test_old():\n    assert True\n")
    _green_cycle(proj)  # 전체 스위트 실행에서 test_old도 처음 통과 — 하지만 세션 첫 실행이 아니므로 fresh_pass
    st = proj.state()
    assert "test_old" in st["premature"] and st["no_red_pending"] == []


# ---- 2단계 (b): red 상태에서 사이클당 소스 증가 한도 ----------------------------------------

def test_growth_over_limit_blocked_until_big_step(proj):
    proj.write("tests/test_a.py", "from m import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    (proj.root / "m.py").write_text("def add(a, b):\n    pass\n")
    assert proj.red_check("tests/test_a.py")[0] == 0
    big = "def add(a, b):\n    return a + b\n\n" + "\n".join(f"def helper{i}():\n    return {i}\n" for i in range(12))
    assert tdd_state.nonblank(big) - 2 > tdd_state.SRC_GROWTH_LIMIT
    d, why = proj.write("m.py", big)
    assert d == "deny" and "한도" in why and "--big-step" in why
    # 여러 번에 나눠 써도 사이클 누적으로 잰다
    assert proj.write("m.py", "def add(a, b):\n    return a + b\n\n" + "\n".join(f"def h{i}():\n    return {i}\n" for i in range(5)))[0] == "allow"
    d, _ = proj.write("m.py", (proj.root / "m.py").read_text() + "\n".join(f"def g{i}():\n    return {i}\n" for i in range(5)))
    assert d == "deny"
    code, _ = proj.red_check("--big-step")
    assert code == 3  # 이유 필수
    code, _ = proj.red_check("--big-step", "자료구조 골격이 한 번에 필요")
    assert code == 0
    assert proj.write("m.py", big)[0] == "allow"
    code, outp = proj.red_check()
    assert code == 1 and "큰 걸음 선언" in outp
    assert proj.state()["big_step"] is None and proj.state()["big_steps"] == 1


def test_small_green_step_allowed_and_refactor_window_unchanged(proj):
    _green_cycle(proj)
    assert proj.write("m.py", "def add(a, b):\n    return sum((a, b))\n")[0] == "deny"  # green: RED 필요
    assert proj.red_check("--refactor")[0] == 0
    assert proj.write("m.py", "def add(a, b):\n    return sum((a, b))\n")[0] == "allow"
    assert proj.red_check()[0] == 1 and proj.state()["state"] == "green"


def test_big_step_only_in_red(proj):
    assert proj.red_check("--big-step", "이유")[0] == 3


def test_shell_write_with_unseen_content_in_red_is_counted_not_blocked(proj):
    proj.write("tests/test_a.py", "from m import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    (proj.root / "m.py").write_text("def add(a, b):\n    pass\n")
    assert proj.red_check("tests/test_a.py")[0] == 0
    d, _ = proj.decision("Bash", command="sed -i 's/pass/return a + b/' m.py")
    assert d == "allow" and proj.state()["shell_unseen"] == 1


def test_stub_only_in_red_missing_unchanged(proj):
    proj.write("tests/test_a.py", "from m import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    assert proj.red_check("tests/test_a.py")[0] == 2  # ModuleNotFoundError
    d, why = proj.write("m.py", "def add(a, b):\n    return a + b\n")
    assert d == "deny" and "스텁" in why
    assert proj.write("m.py", "def add(a, b):\n    pass\n")[0] == "allow"
    assert proj.red_check("tests/test_a.py")[0] == 0


# ---- 3단계: 첫 거부에 SKILL.md 본문을 한 번 붙인다 ------------------------------------------

def test_first_deny_carries_skill_body_once(proj):
    d, why = proj.write("m.py", "x = 1\n")
    assert d == "deny" and "tdd-cycle 절차 (SKILL.md)" in why and "## 사이클" in why
    assert "<이 스킬 디렉터리>" not in why and str(RED_CHECK) in why
    d, why2 = proj.write("m.py", "x = 1\n")
    assert d == "deny" and "SKILL.md" not in why2


def test_skill_tool_call_suppresses_injection(proj):
    assert proj.pre("Skill", skill="tdd-cycle", args="feed") is None
    d, why = proj.write("m.py", "x = 1\n")
    assert d == "deny" and "tdd-cycle 절차" not in why


def test_test_file_writes_are_never_blocked(proj):
    assert proj.write("tests/test_z.py", "def test_z():\n    assert 1\n")[0] == "allow"
    assert "tests/test_z.py" in proj.state()["touched_tests"]


# ---- 호환: 1.1.0 상태 파일 ----------------------------------------------------------

def test_old_state_file_without_new_keys_still_works(proj):
    p = tdd_state.state_path(proj.root)
    old = {"session_id": "s1", "mode": "project", "state": "green", "failing": {}, "passed_once": ["t"], "seen_red": ["t"],
           "premature": [], "runs": 2, "cycles": 1, "missing_to_green": 0, "refactors": 0, "blocks": 0, "log": [], "created": 0}
    p.write_text(json.dumps(old))
    d, why = proj.write("m.py", "x = 1\n")
    assert d == "deny" and "green" in why
    assert "RED 없음 기록" not in proj.red_check("--status")[1]  # 새 카운터가 0이면 요약은 1.1.0 그대로


def test_stop_summary_lists_new_counters_only_when_used(proj):
    _green_cycle(proj)
    proj.write("tests/test_b.py", "from m import add\ndef test_add_zero():\n    assert add(0, 0) == 0\n")
    proj.red_check("tests/test_b.py")
    proj.red_check("--ack", "test_add_zero")
    r = proj.hook("Stop")
    assert "RED 없음 기록(ack) 1" in r["systemMessage"]
