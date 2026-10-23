"""gate-eval 공용 유틸: claude -p 실행, 스트림 파싱, 트랜스크립트 생성."""
from __future__ import annotations

import glob
import json
import os
import subprocess
import time
from pathlib import Path

ALLOWED_TOOLS = "Bash,Read,Edit,Write,MultiEdit,Grep,Glob,Skill,TodoWrite,Task"


def clean_env() -> dict:
    # CLAUDECODE가 있으면 중첩 실행이 거부된다. 프로그램적 서브프로세스는 안전.
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def claude_version() -> str:
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"unknown ({e})"


def find_skill_creator() -> Path | None:
    pats = [
        os.path.expanduser("~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator"),
        os.path.expanduser("~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator"),
    ]
    for p in pats:
        hits = sorted(glob.glob(p), key=os.path.getmtime, reverse=True)
        if hits:
            return Path(hits[0])
    return None


def parse_frontmatter(skill_md: Path) -> tuple[str, str, str]:
    if not skill_md.exists():  # 훅 전용 플러그인: 이름은 디렉터리 이름, description·본문 없음
        return skill_md.parent.name, "", ""
    text = skill_md.read_text()
    if not text.startswith("---"):
        raise ValueError(f"frontmatter 없음: {skill_md}")
    _, fm, body = text.split("---", 2)
    name = desc = ""
    lines = fm.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("\"'")
        elif line.startswith("description:"):
            val = line.split(":", 1)[1].strip()
            if val in (">", "|", ">-", "|-"):
                buf = []
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                    buf.append(lines[i].strip())
                    i += 1
                desc = " ".join(b for b in buf if b)
                continue
            desc = val.strip("\"'")
        i += 1
    return name, desc, body


def run_claude(prompt: str, cwd: Path, model: str, timeout: int, max_turns: int,
               setting_sources: str = "project", extra: list[str] | None = None, persist: bool = False) -> dict:
    """claude -p를 stream-json으로 실행. events, result, duration을 돌려준다.
    persist=True면 세션 트랜스크립트를 남긴다(transcript_path를 읽는 Stop 훅용; --no-session-persistence면 파일이 없다,
    2026-10-23 확인). 끝나면 그 트랜스크립트를 지운다."""
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        *([] if persist else ["--no-session-persistence"]),
        "--setting-sources", setting_sources,
        "--strict-mcp-config",
        "--max-turns", str(max_turns),
        "--allowedTools", ALLOWED_TOOLS,
    ]
    if extra:
        cmd += extra
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=clean_env(), capture_output=True, text=True, timeout=timeout)
        stdout, stderr, timed_out = proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        timed_out = True
    duration_ms = int((time.time() - t0) * 1000)
    events = []
    result = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(ev)
        if ev.get("type") == "result":
            result = ev
    if persist:
        sid = next((e.get("session_id") for e in events if e.get("session_id")), None)
        if sid:
            for f in glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl")):
                os.remove(f)
    return {"events": events, "result": result, "duration_ms": duration_ms,
            "timed_out": timed_out, "stderr": stderr[-2000:]}


def _trunc(s: str, n: int) -> str:
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f"\n…[+{len(s) - n} chars]"


def transcript_md(events: list[dict], prompt: str, tool_in_limit: int = 800, tool_out_limit: int = 2500) -> str:
    """스트림 이벤트를 grader가 읽을 압축 트랜스크립트로."""
    out = [f"# Prompt\n\n{prompt}\n", "# Transcript\n"]
    step = 0
    for ev in events:
        t = ev.get("type")
        if t == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "text" and c.get("text", "").strip():
                    step += 1
                    out.append(f"## Step {step} — assistant text\n\n{_trunc(c['text'], 3000)}\n")
                elif c.get("type") == "tool_use":
                    step += 1
                    out.append(f"## Step {step} — tool_use: {c.get('name')}\n\n```json\n{_trunc(c.get('input', {}), tool_in_limit)}\n```\n")
        elif t == "user":
            for c in ev.get("message", {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    content = c.get("content")
                    if isinstance(content, list):
                        content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
                    out.append(f"### tool_result{' (error)' if c.get('is_error') else ''}\n\n```\n{_trunc(content or '', tool_out_limit)}\n```\n")
        elif t == "result":
            out.append(f"# Final result\n\n{_trunc(ev.get('result', ''), 4000)}\n")
    return "\n".join(out)


def skill_invoked(events: list[dict], skill_name: str) -> bool:
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") != "tool_use":
                continue
            inp = c.get("input", {}) or {}
            if c.get("name") == "Skill" and skill_name in str(inp.get("skill", "")):
                return True
            if c.get("name") == "Read" and f"/{skill_name}/SKILL.md" in str(inp.get("file_path", "")):
                return True
    return False


def usage_summary(result: dict | None) -> dict:
    if not result:
        return {"total_context_tokens": None, "output_tokens": None, "cost_usd": None, "models": []}
    u = result.get("usage", {}) or {}
    total = sum(int(u.get(k, 0) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    return {
        "total_context_tokens": total,
        "uncached_input_tokens": u.get("input_tokens"),
        "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": u.get("cache_read_input_tokens"),
        "output_tokens": u.get("output_tokens"),
        "cost_usd": result.get("total_cost_usd"),
        "num_turns": result.get("num_turns"),
        "models": sorted((result.get("modelUsage") or {}).keys()),
        "is_error": result.get("is_error"),
    }


def approx_tokens(text: str) -> int:
    """토크나이저 없음. 영문 ~4자/토큰, 한글은 더 비쌈(~1.5자/토큰)으로 근사."""
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    other = len(text) - ascii_chars
    return int(ascii_chars / 4 + other / 1.5)
