#!/usr/bin/env python3
"""재현 명령을 실행하고 "올바른 이유로 실패하는지" 판정한다 (SWE-Doctor 아이디어).

사용법:
  python3 repro_check.py --issue "<이슈 텍스트>" [--issue-file 경로] [--timeout 120] -- <명령...>
  예) python3 repro_check.py --issue "slugify('Hello World!') returns 'hello-world-' ..." \\
        -- python3 -c "from slugger import slugify; assert slugify('Hello World!')=='hello-world'"

판정 (정확히 하나, 프로세스 종료 코드):
  REPRODUCED          (0) 비정상 종료 + AssertionError/예외/pytest FAILED + 이슈 키워드가 실패 출력에 등장
  NOT_REPRODUCED      (1) 명령이 성공(exit 0). 보고된 동작이 일어나지 않았다
  ENV_ERROR           (2) 대상 코드에 닿기 전에 실패. import/구문 오류, 파일·모듈·테스트 없음,
                          pytest 수집 오류, command not found, 타임아웃 → 버그 재현이 아니다
  FAILED_OTHER_REASON (3) 진짜 실패지만 이슈 키워드와 겹치지 않음 (다른 테스트가 깨진 경우 등)

출력: 컴팩트 JSON(verdict, exit_code, failure_kind, failure_line, issue_keywords_hit, hit_ratio, tail)
      + 마지막 줄 `[repro-check] verdict=... exit=...`. 표준 라이브러리만 사용.
"""
import argparse
import json
import re
import subprocess
import sys

STOP = {"the", "and", "should", "returns", "return", "when", "with", "this", "that",
        "file", "line", "please", "fix", "bug", "instead", "like"}
MAXLEN = 160

# 환경 문제 패턴: 대상 동작에 도달하기 전에 죽은 흔적
ENV_PATTERNS = [
    (r"\bModuleNotFoundError\b|\bImportError\b", "import_error"),
    (r"\bSyntaxError\b|\bIndentationError\b", "import_error"),
    (r"FileNotFoundError.*\.py\b|can't open file", "import_error"),
    (r"ERROR collecting|no tests ran|ERROR: not found:|ERROR: file or directory not found|"
     r"command not found|No such file or directory", "collection_error"),
]
EXC_RE = re.compile(r"^(?:[\w.]+\.)?(\w+(?:Error|Exception|Exit|Interrupt|Warning))\b(?::|$)")
FAILED_RE = re.compile(r"^FAILED\b|\bFAILED\b.*::|::.*\bFAILED\b")


def extract_keywords(issue: str) -> list[str]:
    """이슈 텍스트에서 식별자(3자+), 따옴표 문자열, 숫자를 뽑고 불용어를 제거한다."""
    kws = set()
    for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", issue):
        kws.add((a or b).strip())
    for w in re.findall(r"\w{3,}", issue):
        if not w.isdigit():
            kws.add(w)
    kws.update(re.findall(r"\d+(?:\.\d+)?", issue))
    return sorted((k for k in kws if k and k.lower() not in STOP), key=len, reverse=True)


def run(cmd: list[str], timeout: int) -> tuple[int | None, str, str | None]:
    """명령 실행. (exit_code, 합쳐진 출력, 실행 자체의 오류 종류) 반환."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, text=True, errors="replace")
        return p.returncode, p.stdout, None
    except subprocess.TimeoutExpired as e:
        out = e.output.decode(errors="replace") if isinstance(e.output, bytes) else (e.output or "")
        return None, out, "timeout"
    except (FileNotFoundError, PermissionError) as e:
        return 127, f"command not found: {cmd[0]} ({e.__class__.__name__})", "command_not_found"


def classify(code, out, run_err, cmd, kws):
    lines = [l.rstrip() for l in out.splitlines() if l.strip()]
    res = {"verdict": None, "exit_code": code, "failure_kind": "none", "failure_line": "",
           "issue_keywords_hit": [], "hit_ratio": 0.0,
           "tail": [l[:MAXLEN] for l in lines[-3:]]}
    if run_err == "timeout":
        res.update(verdict="ENV_ERROR", failure_kind="timeout", failure_line="timed out")
        return res
    if run_err == "command_not_found":
        res.update(verdict="ENV_ERROR", failure_kind="collection_error", failure_line=out[:MAXLEN])
        return res
    if code == 0:
        res["verdict"] = "NOT_REPRODUCED"
        return res

    failed = [l for l in lines if FAILED_RE.search(l)]
    exc = [l for l in lines if EXC_RE.match(l.strip())]
    is_pytest = any("pytest" in a for a in cmd)

    if failed:  # pytest FAILED 줄이 있으면 테스트는 실행된 것 → 실패로 취급
        res.update(failure_kind="pytest_failed", failure_line=failed[-1].strip()[:MAXLEN])
    else:
        for pat, kind in ENV_PATTERNS:  # 대상에 닿기 전 환경 오류
            hit = [l for l in lines if re.search(pat, l)]
            if hit:
                res.update(verdict="ENV_ERROR", failure_kind=kind, failure_line=hit[-1].strip()[:MAXLEN])
                return res
        if is_pytest and code in (2, 3, 4, 5):
            res.update(verdict="ENV_ERROR", failure_kind="collection_error",
                       failure_line=(lines[-1] if lines else f"pytest exit {code}")[:MAXLEN])
            return res
        if exc:
            name = EXC_RE.match(exc[-1].strip()).group(1)
            res.update(failure_kind="assertion" if name == "AssertionError" else f"exception:{name}",
                       failure_line=exc[-1].strip()[:MAXLEN])
        else:
            res.update(failure_kind="exception:Unknown",
                       failure_line=(lines[-1] if lines else f"exit {code}")[:MAXLEN])

    # 이슈 키워드와 실패 출력의 겹침 → 이 실패가 보고된 이슈와 관련 있는가
    low = out.lower()  # 숫자는 토큰 단위(3이 30에 걸리지 않게), 나머지는 부분 문자열로 대조
    hits = [k for k in kws if (re.search(rf"(?<![\w.]){re.escape(k)}(?![\w.])", low)
                               if re.fullmatch(r"[\d.]+", k) else k.lower() in low)]
    res.update(issue_keywords_hit=hits[:6], hit_ratio=round(len(hits) / len(kws), 2) if kws else 0.0)
    res["verdict"] = "REPRODUCED" if hits else "FAILED_OTHER_REASON"
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="재현 명령이 올바른 이유로 실패하는지 판정")
    ap.add_argument("--issue", default="", help="이슈 텍스트")
    ap.add_argument("--issue-file", help="이슈 텍스트 파일 (--issue에 덧붙임)")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="-- 뒤에 재현 명령")
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    issue = a.issue + ("\n" + open(a.issue_file, encoding="utf-8").read() if a.issue_file else "")
    if not cmd or not issue.strip():
        ap.error("--issue(또는 --issue-file)와 -- 뒤의 명령이 모두 필요하다")

    code, out, run_err = run(cmd, a.timeout)
    res = classify(code, out, run_err, cmd, extract_keywords(issue))
    print("{\n" + ",\n".join(f'  "{k}": {json.dumps(v, ensure_ascii=False)}' for k, v in res.items()) + "\n}")
    print(f"[repro-check] verdict={res['verdict']} exit={res['exit_code']}")
    return {"REPRODUCED": 0, "NOT_REPRODUCED": 1, "ENV_ERROR": 2, "FAILED_OTHER_REASON": 3}[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
