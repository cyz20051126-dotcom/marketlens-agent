from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from marketlens.agent.models import FinanceAssumption, FinanceMetric, FinanceScenario
from marketlens.agent.runtime import ToolResponse


def load_finance_metrics(path: Path) -> list[FinanceMetric]:
    metrics: list[FinanceMetric] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            source_evidence_ids = [
                item.strip()
                for item in raw["source_evidence_ids"].split(";")
                if item.strip()
            ]
            metrics.append(
                FinanceMetric(
                    metric_id=raw["metric_id"],
                    brand_id=raw["brand_id"],
                    metric_name=raw["metric_name"],
                    metric_value=float(raw["metric_value"]),
                    unit=raw["unit"],
                    period=raw["period"],
                    formula=raw["formula"],
                    source_evidence_ids=source_evidence_ids,
                    confidence=float(raw["confidence"]),
                    notes=raw.get("notes", ""),
                )
            )
    return metrics


class FinanceModelTool:
    name = "FinanceModelTool"
    description = "Build simple assumption and scenario outputs from finance metrics."

    def __init__(self, metrics: list[FinanceMetric]) -> None:
        self.metrics = list(metrics)

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        brand_id = str(payload.get("brand_id", "") or "")
        brand_metrics = [metric for metric in self.metrics if metric.brand_id == brand_id]
        if not brand_metrics:
            return ToolResponse(False, {}, f"No finance metrics for brand_id: {brand_id}")

        assumptions = [
            FinanceAssumption(
                assumption_id=_assumption_id(metric.metric_id, index),
                brand_id=metric.brand_id,
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                unit=metric.unit,
                period=metric.period,
                formula=metric.formula,
                source_evidence_ids=list(metric.source_evidence_ids),
                confidence=metric.confidence,
                notes=metric.notes,
            ).to_dict()
            for index, metric in enumerate(brand_metrics, start=1)
        ]

        revenue_growth = _base_revenue_growth(brand_metrics)
        operating_margin = _base_operating_margin(brand_metrics)
        scenarios = [
            _scenario(
                scenario_id="fs_001",
                brand_id=brand_id,
                scenario_name="Conservative",
                revenue_growth=revenue_growth - 0.05,
                operating_margin=max(operating_margin - 0.02, 0.01),
                discount_rate=0.14,
                terminal_growth=0.02,
            ),
            _scenario(
                scenario_id="fs_002",
                brand_id=brand_id,
                scenario_name="Base",
                revenue_growth=revenue_growth,
                operating_margin=operating_margin,
                discount_rate=0.12,
                terminal_growth=0.03,
            ),
            _scenario(
                scenario_id="fs_003",
                brand_id=brand_id,
                scenario_name="Upside",
                revenue_growth=revenue_growth + 0.08,
                operating_margin=operating_margin + 0.02,
                discount_rate=0.11,
                terminal_growth=0.035,
            ),
        ]

        return ToolResponse(
            True,
            {
                "brand_id": brand_id,
                "assumptions": assumptions,
                "scenarios": [scenario.to_dict() for scenario in scenarios],
            },
        )


def _assumption_id(metric_id: str, index: int) -> str:
    suffix = metric_id.removeprefix("FM-").lower()
    return f"fa_{suffix}" if suffix else f"fa_{index:03d}"


def _base_revenue_growth(metrics: list[FinanceMetric]) -> float:
    for metric in metrics:
        if metric.unit == "ratio" and "revenue_growth" in metric.metric_name:
            return metric.metric_value
    for metric in metrics:
        if metric.unit == "ratio" and "growth" in metric.metric_name:
            return metric.metric_value
    return 0.08


def _base_operating_margin(metrics: list[FinanceMetric]) -> float:
    for metric in metrics:
        if metric.unit == "ratio" and "operating_margin" in metric.metric_name:
            return metric.metric_value
    return 0.08


def _scenario(
    scenario_id: str,
    brand_id: str,
    scenario_name: str,
    revenue_growth: float,
    operating_margin: float,
    discount_rate: float,
    terminal_growth: float,
) -> FinanceScenario:
    denominator = max(discount_rate - terminal_growth, 0.01)
    result_value = ((1 + revenue_growth) * operating_margin) / denominator
    return FinanceScenario(
        scenario_id=scenario_id,
        brand_id=brand_id,
        scenario_name=scenario_name,
        revenue_growth=round(revenue_growth, 4),
        operating_margin=round(operating_margin, 4),
        discount_rate=discount_rate,
        terminal_growth=terminal_growth,
        sensitivity_axis_x="revenue_growth",
        sensitivity_axis_y="operating_margin",
        result_value=round(result_value, 4),
        notes="DCF-style sensitivity using growth, margin, discount rate, and terminal growth.",
    )
