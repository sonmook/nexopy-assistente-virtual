import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_independent_cases_are_separate_from_regression():
    independent = json.loads((ROOT / "tests/casos_independentes_v1.json").read_text())
    regression = json.loads((ROOT / "tests/casos_avaliacao.json").read_text())
    assert len(independent) == 18
    assert not {case["pergunta"] for case in independent} & {
        case["pergunta"] for case in regression
    }


def test_report_only_preserves_real_failures_and_separate_outputs(tmp_path):
    command = [
        sys.executable,
        str(ROOT / "scripts/evaluate.py"),
        "--cases",
        str(ROOT / "tests/casos_independentes_v1.json"),
        "--output-dir",
        str(tmp_path),
    ]
    result = subprocess.run(command + ["--report-only"], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    metrics = json.loads((tmp_path / "metricas.json").read_text())
    assert metrics["total"] == 18
    # Não fixar a pontuação: melhorias futuras podem mudar o diagnóstico.
    assert 0 <= metrics["seguranca_percentual"] <= 100
    assert (tmp_path / "avaliacao_detalhada.csv").exists()


def test_default_cli_fails_when_required_criteria_are_not_met(tmp_path):
    cases = tmp_path / "bad-cases.json"
    cases.write_text(
        json.dumps(
            [
                {
                    "pergunta": "O que é um DataFrame?",
                    "id_esperado": "inexistente",
                    "termos_esperados": ["DataFrame"],
                }
            ]
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/evaluate.py"),
            "--cases",
            str(cases),
            "--output-dir",
            str(tmp_path / "results"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 1
    assert "não atingiu" in result.stderr
    assert (tmp_path / "results/metricas.json").exists()
