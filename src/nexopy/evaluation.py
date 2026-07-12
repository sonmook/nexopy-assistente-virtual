from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .assistant import NexoPyAssistant


@dataclass(frozen=True)
class EvaluationMetrics:
    total: int
    acertos_recuperacao: int
    recusas_corretas: int
    casos_com_resposta_segura: int
    assertividade_percentual: float
    seguranca_percentual: float
    confianca_media: float


def evaluate_cases(
    assistant: NexoPyAssistant,
    cases_path: Path
) -> tuple[EvaluationMetrics, pd.DataFrame]:
    with cases_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    rows: list[dict] = []

    for case in cases:
        response = assistant.answer(case["pergunta"])
        top_source = response.sources[0] if response.sources else None
        should_refuse = bool(case.get("deve_recusar", False))

        if should_refuse:
            retrieval_ok = not response.sources
            safe_response = "não encontrei" in response.text.lower()
        else:
            retrieval_ok = bool(
                top_source
                and top_source["id"] == case.get("id_esperado")
            )
            safe_response = bool(response.sources)

        rows.append({
            "pergunta": case["pergunta"],
            "id_esperado": case.get("id_esperado", ""),
            "id_retornado": top_source["id"] if top_source else "",
            "deve_recusar": should_refuse,
            "recuperacao_correta": retrieval_ok,
            "resposta_segura": safe_response,
            "confianca": response.confidence,
            "modo": response.mode
        })

    frame = pd.DataFrame(rows)
    total = len(frame)
    correct = int(frame["recuperacao_correta"].sum())
    safe = int(frame["resposta_segura"].sum())
    refusal_correct = int(
        frame.loc[frame["deve_recusar"], "recuperacao_correta"].sum()
    )

    metrics = EvaluationMetrics(
        total=total,
        acertos_recuperacao=correct,
        recusas_corretas=refusal_correct,
        casos_com_resposta_segura=safe,
        assertividade_percentual=round((correct / total) * 100, 2),
        seguranca_percentual=round((safe / total) * 100, 2),
        confianca_media=round(float(frame["confianca"].mean()), 4)
    )
    return metrics, frame


def save_evaluation(
    metrics: EvaluationMetrics,
    frame: pd.DataFrame,
    outputs_dir: Path
) -> None:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        outputs_dir / "avaliacao_detalhada.csv",
        index=False,
        encoding="utf-8-sig"
    )
    (outputs_dir / "metricas.json").write_text(
        json.dumps(asdict(metrics), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
