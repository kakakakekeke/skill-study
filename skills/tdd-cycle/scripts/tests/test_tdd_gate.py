"""tdd_gate.py·tdd_state.py·red_check.py 단위 테스트(1.1.1 결함 수정 2건 + 기존 경로 회귀).
훅은 Claude Code가 주는 stdin JSON 형식으로 구동한다. 실행: python3 -m pytest skills/tdd-cycle/scripts/tests -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
GATE = SKILL / "hooks" / "tdd_gate.py"
RED_CHECK = SKILL / "scripts" / "red_check.py"
sys.path.insert(0, str(SKILL / "scripts"))
import tdd_state  # noqa: E402


@pytest.fixture
def proj(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "__init__.py").write_text("")
    state_dir = tmp_path / "state"
    env = {**os.environ, "TDD_MODE": "1", "TDD_CYCLE_STATE_DIR": str(state_dir), "PYTHONDONTWRITEBYTECODE": "1"}
    for k in ("PYTEST_PLUGINS", "RUNLOG_DIR"):
        env.pop(k, None)
    tdd_state.STATE_DIR = state_dir

    class P:
        def hook(self, event, **kw):
            data = {"hook_event_name": event, "session_id": "s1", "cwd": str(root), **kw}
            r = subprocess.run([sys.executable, str(GATE)], input=json.dumps(data), capture_output=True, text=True, env=env, cwd=root, timeout=30)
            assert r.returncode == 0 and "tdd_gate:" not in r.stderr, r.stderr
            return json.loads(r.stdout) if r.stdout.strip() else None

        def decision(self, tool, **inp):
            r = self.hook("PreToolUse", tool_name=tool, tool_input=inp)
            if r is None:
                return "allow", ""
            h = r["hookSpecificOutput"]
            return h.get("permissionDecision", "allow"), h.get("permissionDecisionReason", "")

        def write(self, rel, content):
            d, why = self.decision("Write", file_path=str(root / rel), content=content)
            if d == "allow":
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(content)
            return d, why

        def post_bash(self, command, stdout):
            return self.hook("PostToolUse", tool_name="Bash", tool_input={"command": command}, tool_response={"stdout": stdout, "stderr": ""})

        def red_check(self, *args):
            r = subprocess.run([sys.executable, str(RED_CHECK), *args], capture_output=True, text=True, env=env, cwd=root, timeout=120)
            return r.returncode, r.stdout + r.stderr

        def state(self):
            return tdd_state.load(root)

    p = P()
    p.root = root
    p.hook("UserPromptSubmit", prompt="README대로 구현해줘")
    return p


# ---- 결함 1: 내장 타입 속성 오류를 '누락'으로 오분류 → 스텁만 허용 상태에 갇힘 -------------------------

@pytest.mark.parametrize("msg,missing", [
    ("AttributeError: 'NoneType' object has no attribute 'strip'", False),
    ("AttributeError: 'str' object has no attribute 'append'", False),
    ("AttributeError: 'list' object has no attribute 'items'", False),
    ("AttributeError: module 'feedparse' has no attribute 'parse_feed'", True),
    ("AttributeError: type object 'Store' has no attribute 'load'", True),
    ("AttributeError: 'Item' object has no attribute 'summary'", True),
    ("ModuleNotFoundError: No module named 'feedparse'", True),
    ("NameError: name 'parse' is not defined", True),
    ("TypeError: parse_feed() got an unexpected keyword argument 'strict'", True),
    ("assert None == []", False),
    ("", False),
])
def test_is_missing_classification(msg, missing):
    assert tdd_state.is_missing(msg) is missing


def test_none_attribute_error_is_behavior_red_not_stub_only(proj):
    """1.1.0 결함 재현: link 없는 item → findtext()가 None → None.strip() → 훅이 '잘못된 이유'로 보고 스텁만 허용 → 모델이 멈춤."""
    proj.write("tests/test_a.py", "from m import links\ndef test_skip_missing():\n    assert links([None, 'a']) == ['a']\n")
    (proj.root / "m.py").write_text("def links(xs):\n    return [x.strip() for x in xs]\n")
    code, out = proj.red_check("tests/test_a.py")
    assert code == 0 and "RED (동작)" in out and "NoneType" in out
    assert proj.state()["state"] == "red"
    d, _ = proj.write("m.py", "def links(xs):\n    return [x.strip() for x in xs if x]\n")
    assert d == "allow"


def test_module_attribute_error_still_stub_only(proj):
    proj.write("tests/test_a.py", "import m\ndef test_a():\n    assert m.add(1, 2) == 3\n")
    (proj.root / "m.py").write_text("")
    code, _ = proj.red_check("tests/test_a.py")
    assert code == 2 and proj.state()["state"] == "red_missing"
    d, why = proj.write("m.py", "def add(a, b):\n    return a + b\n")
    assert d == "deny" and "스텁" in why
    assert proj.write("m.py", "def add(a, b):\n    pass\n")[0] == "allow"


def test_bash_pytest_output_with_none_attribute_counts_as_red(proj):
    proj.post_bash("python3 -m pytest tests -q", "FAILED tests/test_a.py::test_a - AttributeError: 'NoneType' object has no attribute 'strip'\n1 failed in 0.1s")
    assert proj.state()["state"] == "red"


# ---- 결함 2: 출력을 잘라서 못 읽은 pytest 뒤 앞의 RED가 남아 수정이 계속 허용됨 → unknown ----------------

def test_unreadable_pytest_output_blocks_until_rerun(proj):
    proj.write("tests/test_a.py", "from m import f\ndef test_a():\n    assert f() == 1\n")
    (proj.root / "m.py").write_text("def f():\n    pass\n")
    assert proj.red_check("tests/test_a.py")[0] == 0 and proj.state()["state"] == "red"
    r = proj.post_bash("python -m pytest tests/test_a.py -q 2>&1 | tail -1", "assert None == 1")
    assert proj.state()["state"] == "unknown" and "읽지 못했다" in r["hookSpecificOutput"]["additionalContext"]
    d, why = proj.write("m.py", "def f():\n    return 1\n")
    assert d == "deny" and "읽지 못했다" in why
    assert proj.red_check("tests/test_a.py")[0] == 0 and proj.state()["state"] == "red"
    assert proj.write("m.py", "def f():\n    return 1\n")[0] == "allow"
    assert "결과 못 읽은 pytest 1" in proj.red_check("--status")[1]


@pytest.mark.parametrize("cmd,expected", [
    ("python -m pytest tests -q", True), ("pytest tests/test_a.py::test_a -x", True), ("cd proj && pytest", True),
    ("PYTHONPATH=. pytest tests -q", True), ("uv run pytest tests", True), ("timeout 60 pytest tests", True),
    ("pytest tests -q 2>&1 | tail -3", True),
    ("pytest --version", False), ("pip install pytest", False), ("pytest --collect-only -q", False),
    ("echo pytest", False), ("grep -n pytest pyproject.toml", False),
    ("cat > tests/test_a.py <<'EOF'\nimport pytest\n\ndef test_a():\n    pass\nEOF", False),
    ("cat > tests/test_a.py <<'EOF'\nimport pytest\nEOF\npytest tests/test_a.py", True),
])
def test_runs_pytest_detection(cmd, expected):
    assert tdd_state.runs_pytest(cmd) is expected


def test_pytest_mention_without_run_does_not_change_state(proj):
    proj.post_bash("cat > tests/test_b.py <<'EOF'\nimport pytest\n\ndef test_b():\n    assert 1\nEOF", "")
    proj.post_bash("grep -n pytest pyproject.toml", "[tool.pytest.ini_options]")
    assert proj.state()["state"] == "none"


def test_no_tests_ran_is_not_unknown(proj):
    proj.post_bash("pytest -q", "no tests ran in 0.01s")
    assert proj.state()["state"] == "none"


def test_unusual_invocation_with_readable_output_still_applies(proj):
    proj.post_bash("./run_tests.sh --runner pytest", "FAILED tests/test_a.py::test_a - assert None == 1\n1 failed in 0.1s")
    assert proj.state()["state"] == "red"


# ---- 기존 경로 회귀 ------------------------------------------------------------------------

def test_green_blocks_and_refactor_window_allows(proj):
    proj.write("tests/test_a.py", "from m import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    (proj.root / "m.py").write_text("def add(a, b):\n    pass\n")
    assert proj.red_check("tests/test_a.py")[0] == 0
    assert proj.write("m.py", "def add(a, b):\n    return a + b\n")[0] == "allow"
    assert proj.red_check()[0] == 1
    assert proj.write("m.py", "def add(a, b):\n    return sum((a, b))\n")[0] == "deny"
    assert proj.red_check("--refactor")[0] == 0
    assert proj.write("m.py", "def add(a, b):\n    return sum((a, b))\n")[0] == "allow"
    assert proj.red_check()[0] == 1 and proj.state()["state"] == "green"


def test_test_file_writes_never_blocked(proj):
    assert proj.write("tests/test_z.py", "def test_z():\n    assert 1\n")[0] == "allow"


def test_old_state_file_loads(proj):
    p = tdd_state.state_path(proj.root)
    p.write_text(json.dumps({"session_id": "s1", "mode": "project", "state": "green", "failing": {}, "passed_once": [], "seen_red": [],
                             "premature": [], "runs": 1, "cycles": 0, "missing_to_green": 0, "refactors": 0, "blocks": 0, "log": [], "created": 0}))
    d, why = proj.write("m.py", "x = 1\n")
    assert d == "deny" and "green" in why
    assert "결과 못 읽은" not in proj.red_check("--status")[1]
