from __future__ import annotations

from statistics import mean

from marketlens.schemas import BrandProfile, BriefSection, EvidenceRow, validate_brand_profile
from marketlens.score import score_evidence


BRAND_STATIC = {
    "luckin": {
        "name": "瑞幸咖啡",
        "category": "coffee",
        "market_position": "以高密度门店和数字化点单支撑高频消费的咖啡连锁。",
        "price_signal": "性价比促销驱动",
        "expansion_model": "门店密度扩张",
        "franchise_model": "联营门店配合总部管控",
        "brand_narrative": "便利、数字化、面向日常消费的咖啡品牌。",
        "risk_signal": "价格竞争与促销依赖",
        "matrix_x": 0.32,
        "matrix_y": 0.42,
    },
    "cotti": {
        "name": "库迪咖啡",
        "category": "coffee",
        "market_position": "以低价和快速铺店挑战现有咖啡连锁格局的进攻型品牌。",
        "price_signal": "低客单价挑战者",
        "expansion_model": "加盟驱动的快速铺店",
        "franchise_model": "加盟为主并配套运营支持",
        "brand_narrative": "通过小店型和高性价比降低咖啡消费门槛。",
        "risk_signal": "利润率压力与品牌差异化不足",
        "matrix_x": 0.24,
        "matrix_y": 0.36,
    },
    "starbucks": {
        "name": "星巴克中国",
        "category": "coffee",
        "market_position": "在高端体验和本土价格竞争之间重新平衡的全球咖啡品牌。",
        "price_signal": "高端定价",
        "expansion_model": "强调体验和质量的稳健扩张",
        "franchise_model": "由直营核心向授权经营过渡",
        "brand_narrative": "以第三空间体验和本地化产品维持品牌溢价。",
        "risk_signal": "本土性价比竞争与客单价压力",
        "matrix_x": 0.67,
        "matrix_y": 0.64,
    },
    "mixue": {
        "name": "蜜雪冰城",
        "category": "tea",
        "market_position": "以极致规模和低价心智占据大众茶饮/冰淇淋市场。",
        "price_signal": "极致性价比",
        "expansion_model": "供应链支撑的加盟规模化",
        "franchise_model": "轻资产加盟网络",
        "brand_narrative": "依靠供应链效率提供日常可负担饮品和冰淇淋。",
        "risk_signal": "加盟质量控制与低价利润约束",
        "matrix_x": 0.18,
        "matrix_y": 0.56,
    },
    "chagee": {
        "name": "霸王茶姬",
        "category": "tea",
        "market_position": "以东方茶文化和高端叙事建立差异化的新茶饮品牌。",
        "price_signal": "高端茶饮",
        "expansion_model": "品牌势能驱动扩张",
        "franchise_model": "加盟与直营结合并强调品牌管控",
        "brand_narrative": "将现代东方茶饮塑造成更具仪式感的消费场景。",
        "risk_signal": "高端茶饮拥挤与海外执行风险",
        "matrix_x": 0.78,
        "matrix_y": 0.80,
    },
    "guming": {
        "name": "古茗",
        "category": "tea",
        "market_position": "以低线城市渗透和区域密度见长的规模化鲜制茶饮品牌。",
        "price_signal": "中端性价比",
        "expansion_model": "区域加盟密度扩张",
        "franchise_model": "加盟网络配合区域化运营",
        "brand_narrative": "让鲜果茶在更广泛城市和商圈中可获得。",
        "risk_signal": "同店竞争与加盟一致性",
        "matrix_x": 0.42,
        "matrix_y": 0.62,
    },
    "chapanda": {
        "name": "茶百道",
        "category": "tea",
        "market_position": "依靠广泛加盟网络触达大众市场的主流新茶饮品牌。",
        "price_signal": "大众价位",
        "expansion_model": "全国加盟扩张",
        "franchise_model": "加盟主导的门店网络",
        "brand_narrative": "以稳定菜单和加盟规模实现广覆盖鲜制茶饮。",
        "risk_signal": "品类饱和与执行一致性",
        "matrix_x": 0.46,
        "matrix_y": 0.58,
    },
}

SECTION_TITLES = {
    "pricing": "价格压力",
    "expansion": "扩张模式",
    "franchise": "加盟运营风险",
    "positioning": "品牌定位",
    "risk": "风险信号",
}

SECTION_SUMMARIES = {
    "pricing": (
        "价格竞争正在从单纯补贴转向更精细的分层运营：瑞幸同店销售增速承压，"
        "库迪收缩全场 9.9 元促销，蜜雪冰城继续用低价产品强化大众心智。"
        "这说明低价仍是获客入口，但持续大范围补贴对利润率和品牌差异化都有压力。"
    ),
    "expansion": (
        "头部品牌的扩张路径明显分化：瑞幸依靠高密度门店继续放大便利性，"
        "库迪以联营/合作模式快速铺量，星巴克中国借合资架构规划更长期的门店增长，"
        "茶饮品牌则更多依赖加盟网络和供应链能力放大规模。"
    ),
    "franchise": (
        "加盟和合作门店是多数品牌扩张的核心杠杆，但也是运营风险的来源。"
        "瑞幸、库迪、蜜雪、古茗和茶百道都需要在速度、总部管控、加盟商执行和门店一致性之间取得平衡。"
    ),
    "positioning": (
        "品牌定位呈现两条主线：一条是瑞幸、库迪、蜜雪代表的高频性价比路线，"
        "另一条是星巴克中国和霸王茶姬代表的体验/高端叙事路线。"
        "古茗和茶百道处在大众茶饮中间带，更依赖门店密度、菜单稳定性和供应链效率。"
    ),
    "risk": (
        "需要重点跟踪三类风险：价格战带来的利润率压力，加盟网络扩张带来的执行一致性压力，"
        "以及供应链和原材料成本对茶饮品牌的影响。低置信度或二手来源结论应保留复核标记。"
    ),
}


def _active_rows(evidence_rows: list[EvidenceRow]) -> list[EvidenceRow]:
    return [row for row in evidence_rows if row.review_status != "rejected"]


def build_brand_profiles(evidence_rows: list[EvidenceRow]) -> list[BrandProfile]:
    active_rows = _active_rows(evidence_rows)
    profiles: list[BrandProfile] = []

    for brand_id, static in BRAND_STATIC.items():
        brand_rows = [row for row in active_rows if row.brand_id == brand_id]
        confidence = mean(score_evidence(row) for row in brand_rows) if brand_rows else 0.0
        profile = BrandProfile(
            brand_id=brand_id,
            name=static["name"],
            category=static["category"],
            market_position=static["market_position"],
            price_signal=static["price_signal"],
            expansion_model=static["expansion_model"],
            franchise_model=static["franchise_model"],
            brand_narrative=static["brand_narrative"],
            risk_signal=static["risk_signal"],
            matrix_x=static["matrix_x"],
            matrix_y=static["matrix_y"],
            evidence_count=len(brand_rows),
            confidence=round(confidence, 4),
        )
        validate_brand_profile(profile)
        profiles.append(profile)

    return profiles


def build_brief_sections(
    evidence_rows: list[EvidenceRow],
    profiles: list[BrandProfile],
) -> list[BriefSection]:
    active_rows = _active_rows(evidence_rows)
    profile_count = len(profiles)
    average_profile_confidence = mean(profile.confidence for profile in profiles) if profiles else 0.0
    total_evidence = sum(profile.evidence_count for profile in profiles)
    overview_ids = [row.evidence_id for row in active_rows[:8]]

    sections = [
        BriefSection(
            section_id="overview",
            title="市场概览",
            summary=(
                f"MarketLens AI 当前跟踪 {profile_count} 个茶饮/咖啡品牌，"
                f"并沉淀了 {total_evidence} 条带来源链接的有效证据。"
            ),
            supporting_evidence_ids=overview_ids,
            confidence=round(average_profile_confidence, 4) if total_evidence else 0.0,
        )
    ]

    for lens, title in SECTION_TITLES.items():
        lens_rows = [row for row in active_rows if row.lens == lens]
        evidence_ids = [row.evidence_id for row in lens_rows[:8]]
        confidence = mean(score_evidence(row) for row in lens_rows) if lens_rows else 0.0
        if lens_rows:
            summary = SECTION_SUMMARIES[lens]
        else:
            summary = f"当前还没有为 {lens} 维度加载已复核证据。"
        sections.append(
            BriefSection(
                section_id=lens,
                title=title,
                summary=summary,
                supporting_evidence_ids=evidence_ids,
                confidence=round(confidence, 4),
            )
        )

    return sections
