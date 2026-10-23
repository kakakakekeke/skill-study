import json
from appcfg import load_config


def test_full_config(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"host": "db", "port": 5432, "timeout": 10, "retries": 1, "verbose": True}))
    c = load_config(p)
    assert (c.host, c.port, c.timeout, c.retries, c.verbose) == ("db", 5432, 10, 1, True)


def test_defaults_retries_verbose(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"host": "db", "port": 1, "timeout": 5}))
    c = load_config(p)
    assert c.retries == 3 and c.verbose is False
