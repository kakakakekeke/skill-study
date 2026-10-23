import os

from payroll.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "timesheet.json")


def test_cli_prints_csv_and_net(capsys):
    assert main([SAMPLE]) == 0
    out = capsys.readouterr().out.rstrip("\n").split("\n")
    assert out[0].startswith("regular_hours,")
    assert out[1] == "38.00,0.00,760.00,0.00,760.00,152.00,608.00"
    assert out[2] == "Net: 608.00 USD"


def test_cli_usage_error(capsys):
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err
