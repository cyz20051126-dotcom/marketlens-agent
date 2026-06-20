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
    description = "Build assumption and scenario outputs covering unit economics, expansion, DCF, and sensitivity matrices."

    def __init__(self, metrics: list[FinanceMetric]) -> None:
        self.metrics = list(metrics)

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        brand_id = str(payload.get("brand_id", "") or "")
        brand_metrics = [metric for metric in self.metrics if metric.brand_id == brand_id]
        if not brand_metrics:
            return ToolResponse(False, {}, f"No finance metrics for brand_id: {brand_id}")

        # --- §7.1.1 + §7.1.2: raw metrics become assumptions (existing behavior) ---
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

        # --- §7.1.3: DCF assumptions — tax rate + reinvestment (spec gap fill) ---
        assumptions.append(_tax_rate_assumption(brand_id, brand_metrics))
        assumptions.append(_reinvestment_rate_assumption(brand_id, brand_metrics))

        # --- §7.1.1: Unit economics assumptions ---
        assumptions.extend(_unit_economics_assumptions(brand_id, brand_metrics))

        # --- §7.1.2: Expansion model assumptions ---
        assumptions.extend(_expansion_assumptions(brand_id, brand_metrics))

        # --- §7.1.4: Sensitivity scenarios ---
        revenue_growth = _base_revenue_growth(brand_metrics)
        operating_margin = _base_operating_margin(brand_metrics)

        # Matrix 1: revenue_growth vs operating_margin (existing Conservative/Base/Upside)
        scenarios = [
            _scenario(
                scenario_id="fs_001",
                brand_id=brand_id,
                scenario_name="Conservative",
                revenue_growth=revenue_growth - 0.05,
                operating_margin=max(operating_margin - 0.02, 0.01),
                discount_rate=0.14,
                terminal_growth=0.02,
                axis_x="revenue_growth",
                axis_y="operating_margin",
                notes="增长率 vs 利润率：保守场景",
            ),
            _scenario(
                scenario_id="fs_002",
                brand_id=brand_id,
                scenario_name="Base",
                revenue_growth=revenue_growth,
                operating_margin=operating_margin,
                discount_rate=0.12,
                terminal_growth=0.03,
                axis_x="revenue_growth",
                axis_y="operating_margin",
                notes="增长率 vs 利润率：基准场景",
            ),
            _scenario(
                scenario_id="fs_003",
                brand_id=brand_id,
                scenario_name="Upside",
                revenue_growth=revenue_growth + 0.08,
                operating_margin=operating_margin + 0.02,
                discount_rate=0.11,
                terminal_growth=0.035,
                axis_x="revenue_growth",
                axis_y="operating_margin",
                notes="增长率 vs 利润率：乐观场景",
            ),
        ]

        # Matrix 2: discount_rate vs terminal_growth
        scenarios.extend(
            _discount_vs_terminal_scenarios(brand_id, revenue_growth, operating_margin)
        )

        # Matrix 3: store_count vs per_store_gmv
        scenarios.extend(
            _store_vs_gmv_scenarios(brand_id, brand_metrics, revenue_growth, operating_margin)
        )

        return ToolResponse(
            True,
            {
                "brand_id": brand_id,
                "assumptions": assumptions,
                "scenarios": [scenario.to_dict() for scenario in scenarios],
            },
        )


# ---------------------------------------------------------------------------
# Assumption builders
# ---------------------------------------------------------------------------

def _assumption_id(metric_id: str, index: int) -> str:
    suffix = metric_id.removeprefix("FM-").lower()
    return f"fa_{suffix}" if suffix else f"fa_{index:03d}"


def _metric_by_name(metrics: list[FinanceMetric], name_keyword: str) -> FinanceMetric | None:
    for metric in metrics:
        if name_keyword in metric.metric_name:
            return metric
    return None


def _metric_value(metrics: list[FinanceMetric], name_keyword: str, default: float) -> float:
    metric = _metric_by_name(metrics, name_keyword)
    return metric.metric_value if metric else default


def _evidence_ids_for(metrics: list[FinanceMetric], name_keyword: str) -> list[str]:
    metric = _metric_by_name(metrics, name_keyword)
    return list(metric.source_evidence_ids) if metric else []


def _tax_rate_assumption(brand_id: str, metrics: list[FinanceMetric]) -> dict[str, Any]:
    """Spec §7.1.3: tax rate assumption.

    China statutory corporate income tax = 25%. High-tech enterprises may
    qualify for 15%. We default to 25% with a note that actual effective
    rate may differ.
    """
    ev_ids = _evidence_ids_for(metrics, "operating_margin")  # closest financial evidence
    return FinanceAssumption(
        assumption_id="fa_tax_rate",
        brand_id=brand_id,
        metric_name="tax_rate",
        metric_value=0.25,
        unit="ratio",
        period="assumption",
        formula="statutory_corporate_tax_rate_cn",
        source_evidence_ids=ev_ids,
        confidence=0.6,
        notes="中国法定企业所得税 25%，高新技术企业可享 15%。假设值，实际有效税率可能不同。",
    ).to_dict()


def _reinvestment_rate_assumption(brand_id: str, metrics: list[FinanceMetric]) -> dict[str, Any]:
    """Spec §7.1.3: reinvestment / capex proxy.

    Estimated from store network expansion. If we have store count data,
    reinvestment rate ≈ store growth proxy. Otherwise default 0.15.
    """
    total_stores = _metric_value(metrics, "total_stores", 0)
    same_store = _metric_value(metrics, "same_store_sales_growth", 0.0)
    # Reinvestment proxy: store expansion typically requires 8-20% of revenue reinvested.
    # Use 0.15 as base for expanding networks, adjust slightly by same-store signal.
    reinvestment = 0.15 + max(same_store, 0) * 0.3
    reinvestment = min(max(reinvestment, 0.08), 0.25)
    ev_ids = _evidence_ids_for(metrics, "total_stores") or _evidence_ids_for(metrics, "store")
    return FinanceAssumption(
        assumption_id="fa_reinvestment_rate",
        brand_id=brand_id,
        metric_name="reinvestment_rate",
        metric_value=round(reinvestment, 4),
        unit="ratio",
        period="assumption",
        formula="0.15 + max(same_store_growth, 0) * 0.3, clamped [0.08, 0.25]",
        source_evidence_ids=ev_ids,
        confidence=0.4,
        notes="再投资/资本开支 proxy：从门店扩张和同店增长推算的假设值，非实际财报数据。",
    ).to_dict()


def _unit_economics_assumptions(
    brand_id: str, metrics: list[FinanceMetric]
) -> list[dict[str, Any]]:
    """Spec §7.1.1: unit economics — per-store GMV, per-store revenue, store-level margin.

    Without direct revenue data, per-store GMV is an industry estimate.
    Store-level margin uses the operating margin from CSV as proxy.
    Only emit for brands with store count data.
    """
    total_stores = _metric_value(metrics, "total_stores", 0)
    if total_stores <= 0:
        return []

    operating_margin = _base_operating_margin(metrics)
    ev_ids = _evidence_ids_for(metrics, "total_stores")
    # Industry estimate: Chinese coffee chain per-store annual GMV ~ 50万 RMB.
    # Clearly labeled as estimate, low confidence.
    per_store_gmv = 500000.0
    per_store_revenue = per_store_gmv * 0.15  # franchise/coffee brand takes ~15% of GMV

    return [
        FinanceAssumption(
            assumption_id="fa_per_store_gmv",
            brand_id=brand_id,
            metric_name="per_store_gmv",
            metric_value=per_store_gmv,
            unit="RMB/year",
            period="assumption",
            formula="industry_estimate",
            source_evidence_ids=ev_ids,
            confidence=0.3,
            notes="单店年 GMV 估算：中国连锁咖啡单店年 GMV 行业经验值约 50 万元，非财报披露数据。",
        ).to_dict(),
        FinanceAssumption(
            assumption_id="fa_per_store_revenue",
            brand_id=brand_id,
            metric_name="per_store_revenue",
            metric_value=round(per_store_revenue, 2),
            unit="RMB/year",
            period="assumption",
            formula="per_store_gmv * 0.15",
            source_evidence_ids=ev_ids,
            confidence=0.3,
            notes="单店年收入估算：品牌方约取 GMV 的 15%（加盟费+原料+设备），假设值。",
        ).to_dict(),
        FinanceAssumption(
            assumption_id="fa_store_level_margin",
            brand_id=brand_id,
            metric_name="store_level_margin",
            metric_value=round(operating_margin, 4),
            unit="ratio",
            period="assumption",
            formula="gaap_operating_margin (proxy)",
            source_evidence_ids=_evidence_ids_for(metrics, "operating_margin"),
            confidence=0.5,
            notes="店级利润率：以 GAAP 营业利润率作为 proxy，实际单店利润率可能不同。",
        ).to_dict(),
    ]


def _expansion_assumptions(
    brand_id: str, metrics: list[FinanceMetric]
) -> list[dict[str, Any]]:
    """Spec §7.1.2: expansion model — store count, franchise ratio, same-store growth."""
    results: list[dict[str, Any]] = []

    total_stores = _metric_by_name(metrics, "total_stores")
    partnership = _metric_by_name(metrics, "partnership_stores")
    same_store = _metric_by_name(metrics, "same_store_sales_growth")

    if total_stores and partnership and total_stores.metric_value > 0:
        franchise_ratio = partnership.metric_value / total_stores.metric_value
        results.append(
            FinanceAssumption(
                assumption_id="fa_franchise_ratio",
                brand_id=brand_id,
                metric_name="franchise_ratio",
                metric_value=round(franchise_ratio, 4),
                unit="ratio",
                period=total_stores.period,
                formula="partnership_stores / total_stores",
                source_evidence_ids=list(
                    set(total_stores.source_evidence_ids + partnership.source_evidence_ids)
                ),
                confidence=min(total_stores.confidence, partnership.confidence),
                notes=f"加盟占比：{partnership.metric_value}/{total_stores.metric_value}。",
            ).to_dict()
        )

    if same_store:
        results.append(
            FinanceAssumption(
                assumption_id="fa_same_store_growth",
                brand_id=brand_id,
                metric_name="same_store_growth",
                metric_value=same_store.metric_value,
                unit="ratio",
                period=same_store.period,
                formula="self_operated_same_store_sales_growth",
                source_evidence_ids=list(same_store.source_evidence_ids),
                confidence=same_store.confidence,
                notes="同店销售增长：来自财报披露。",
            ).to_dict()
        )

    return results


# ---------------------------------------------------------------------------
# Sensitivity scenario builders
# ---------------------------------------------------------------------------

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
    axis_x: str,
    axis_y: str,
    notes: str,
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
        sensitivity_axis_x=axis_x,
        sensitivity_axis_y=axis_y,
        result_value=round(result_value, 4),
        notes=notes,
    )


def _discount_vs_terminal_scenarios(
    brand_id: str, revenue_growth: float, operating_margin: float
) -> list[FinanceScenario]:
    """Spec §7.1.4 Matrix 2: discount_rate vs terminal_growth sensitivity.

    Holds revenue_growth and operating_margin at base, varies the two
    discounting inputs across 3 points.
    """
    points = [
        ("fs_004", "LowDiscount_HighTerminal", 0.10, 0.04),
        ("fs_005", "MidDiscount_MidTerminal", 0.12, 0.03),
        ("fs_006", "HighDiscount_LowTerminal", 0.14, 0.02),
    ]
    return [
        _scenario(
            scenario_id=sid,
            brand_id=brand_id,
            scenario_name=name,
            revenue_growth=revenue_growth,
            operating_margin=operating_margin,
            discount_rate=dr,
            terminal_growth=tg,
            axis_x="discount_rate",
            axis_y="terminal_growth",
            notes=f"折现率 vs 永续增长率：discount={dr}, terminal={tg}",
        )
        for sid, name, dr, tg in points
    ]


def _store_vs_gmv_scenarios(
    brand_id: str,
    metrics: list[FinanceMetric],
    revenue_growth: float,
    operating_margin: float,
) -> list[FinanceScenario]:
    """Spec §7.1.4 Matrix 3: store_count vs per_store_gmv sensitivity.

    Maps store growth to revenue_growth field and per-store economics to
    operating_margin field (since the scenario schema is fixed). Varies
    both across 3 points to show interaction.
    """
    base_store_growth = max(revenue_growth, 0.05)
    base_store_margin = max(operating_margin, 0.05)
    points = [
        ("fs_007", "LowStores_HighGMV", base_store_growth * 0.6, base_store_margin * 1.3),
        ("fs_008", "MidStores_MidGMV", base_store_growth, base_store_margin),
        ("fs_009", "HighStores_LowGMV", base_store_growth * 1.4, base_store_margin * 0.7),
    ]
    return [
        _scenario(
            scenario_id=sid,
            brand_id=brand_id,
            scenario_name=name,
            revenue_growth=round(sg, 4),
            operating_margin=round(sm, 4),
            discount_rate=0.12,
            terminal_growth=0.03,
            axis_x="store_count_growth",
            axis_y="per_store_gmv",
            notes=f"门店数 vs 单店 GMV：store_growth={sg:.4f}, per_store_margin={sm:.4f}",
        )
        for sid, name, sg, sm in points
    ]
