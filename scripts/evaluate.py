from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nexopy.assistant import NexoPyAssistant
from nexopy.config import Settings
from nexopy.evaluation import evaluate_cases, save_evaluation


def main() -> None:
    settings = Settings()
    assistant = NexoPyAssistant(settings=settings, enable_llm=False)

    metrics, details = evaluate_cases(
        assistant=assistant,
        cases_path=settings.evaluation_path
    )
    save_evaluation(metrics, details, settings.outputs_dir)

    print("\nAvaliação do NexoPy")
    print("-" * 50)
    print(f"Total de casos: {metrics.total}")
    print(f"Acertos de recuperação: {metrics.acertos_recuperacao}")
    print(f"Assertividade: {metrics.assertividade_percentual:.2f}%")
    print(f"Respostas seguras: {metrics.seguranca_percentual:.2f}%")
    print(f"Confiança média: {metrics.confianca_media:.4f}")
    print(f"Resultados salvos em: {settings.outputs_dir}")


if __name__ == "__main__":
    main()
