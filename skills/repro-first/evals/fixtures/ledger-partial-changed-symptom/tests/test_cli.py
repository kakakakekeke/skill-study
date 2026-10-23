import os

from ledger.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "invoice.json")


def test_cli_prints_csv_and_total(capsys, tmp_path):
    path = tmp_path / "invoice.json"
    path.write_text('{"items": [{"sku": "A", "unit_price": "19.99", "qty": 3, "tax_rate": "0.0825"}]}')
    assert main([str(path)]) == 0
    out = capsys.readouterr().out.rstrip("\n").split("\n")
    assert out[0] == "sku,qty,net,tax,gross"
    assert out[-2].startswith("TOTAL,,,,")
    assert out[-1].startswith("Total: ") and out[-1].endswith(" USD")
    assert out[-2].split(",")[-1] == out[-1].split()[1]


def test_cli_usage_error(capsys):
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err
