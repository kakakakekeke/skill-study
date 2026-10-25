"""측정용 pytest 플러그인: 모델이 돌린 pytest 실행마다 테스트별 결과를 RUNLOG_DIR/<rootdir 이름>.jsonl에 한 줄로 남긴다.

모델 출력(grep·tail로 걸러질 수 있음)이나 파일 복원(셸 스크립트 편집은 못 따라감)에 기대지 않고
"어떤 테스트가 언제 무슨 이유로 실패·통과했나"를 얻기 위해서다. 출력은 바꾸지 않는다.
켜기: PYTHONPATH=<이 디렉터리> PYTEST_PLUGINS=pytest_runlog RUNLOG_DIR=<기록 디렉터리>
"""
import json
import os
import time

_state = {}


def pytest_sessionstart(session):
    _state.clear()
    _state.update(config=session.config, tests={}, collect_errors=[])


def _msg(report):
    crash = getattr(report.longrepr, "reprcrash", None)
    if crash is not None:
        return crash.message.splitlines()[0][:300] if crash.message else ""
    return str(report.longrepr).strip().splitlines()[-1][:300] if report.longrepr else ""


def pytest_collectreport(report):
    if report.failed and _state:
        _state["collect_errors"].append({"nodeid": report.nodeid, "msg": _msg(report)})


def pytest_runtest_logreport(report):
    if not _state:
        return
    if report.when == "call" or (report.failed and report.when == "setup"):
        _state["tests"][report.nodeid] = {"outcome": report.outcome, "msg": _msg(report) if report.failed else ""}
    elif report.when == "setup" and report.skipped:
        _state["tests"][report.nodeid] = {"outcome": "skipped", "msg": ""}


def pytest_sessionfinish(session, exitstatus):
    d = os.environ.get("RUNLOG_DIR")
    if not d or not _state:
        return
    try:
        root = os.path.basename(str(session.config.rootpath))
        os.makedirs(d, exist_ok=True)
        rec = {"t": time.time(), "root": root, "args": list(session.config.invocation_params.args),
               "exit": int(exitstatus), "tests": _state["tests"], "collect_errors": _state["collect_errors"]}
        with open(os.path.join(d, root + ".jsonl"), "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001  측정 실패가 모델의 pytest를 깨면 안 된다
        pass
