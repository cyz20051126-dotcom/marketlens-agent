from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from marketlens.agent.runtime import BaseAgent, ToolResponse
from marketlens.schemas import (
    ALLOWED_BRANDS,
    ALLOWED_LENSES,
    ALLOWED_SOURCE_TYPES,
    EvidenceRow,
    validate_evidence_row,
)


ZH_VALUATION = "\u4f30\u503c"
ZH_PROFIT_MARGIN = "\u5229\u6da6\u7387"
ZH_GROSS_MARGIN = "\u6bdb\u5229\u7387"
ZH_SINGLE_STORE = "\u5355\u5e97"
ZH_PAYBACK = "\u56de\u672c"
ZH_LATEST = "\u6700\u65b0"
ZH_SEARCH = "\u641c\u7d22"
ZH_ONLINE = "\u4e0a\u7f51"
ZH_SUPPLEMENT = "\u8865\u5145"
ZH_NEWS = "\u65b0\u95fb"
ZH_NEW_INFO = "\u65b0\u8d44\u6599"
ZH_REPORT = "\u62a5\u544a"
ZH_GENERATE = "\u751f\u6210"
ZH_WRITE = "\u64b0\u5199"
ZH_SUMMARY = "\u603b\u7ed3"
ZH_EVIDENCE_INSUFFICIENT = "\u8bc1\u636e\u4e0d\u8db3"
ZH_SENSITIVITY = "\u654f\u611f\u6027\u5206\u6790"
ZH_NOT_INVESTMENT_ADVICE = "\u975e\u6295\u8d44\u5efa\u8bae"
ZH_FOR_QUERY = "\u9488\u5bf9"
ZH_INTENT = "\u7814\u7a76\u610f\u56fe"
ZH_CITED_EVIDENCE = "\u5f15\u7528\u8bc1\u636e"
ZH_SCENARIO_DISCUSSION = "\u5df2\u7eb3\u5165\u573a\u666f\u8ba8\u8bba"

FINANCE_TERMS = (
    "dcf",
    ZH_VALUATION,
    ZH_PROFIT_MARGIN,
    ZH_GROSS_MARGIN,
    ZH_SINGLE_STORE,
    ZH_PAYBACK,
    "margin",
    "valuation",
)
RESEARCH_TERMS = (
    ZH_LATEST,
    ZH_SEARCH,
    ZH_ONLINE,
    ZH_SUPPLEMENT,
    ZH_NEWS,
    "2026",
    ZH_NEW_INFO,
    "latest",
    "search",
    "news",
)
REPORT_TERMS = (ZH_REPORT, ZH_GENERATE, ZH_WRITE, ZH_SUMMARY, "brief", "report")
FINANCE_ASSUMPTION_TERMS = ("dcf", ZH_VALUATION, "valuation")
DEFAULT_LENS = "risk"
DEFAULT_SOURCE_TYPE = "news"
DEFAULT_SOURCE_DATE = "2026-06-20"


class TriageAgent(BaseAgent):
    name = "TriageAgent"

    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = _text(payload.get("query"))
        system_prompt = (
            "\u4f60\u662f\u65b0\u8336\u996e\u54c1\u724c\u7814\u7a76\u610f\u56fe\u5206\u7c7b\u5668\u3002"
            "\u5c06\u7528\u6237\u95ee\u9898\u5206\u4e3a\u4ee5\u4e0b\u610f\u56fe\u4e4b\u4e00\uff1a\n"
            "- finance_analysis_needed: \u6d89\u53ca\u4f30\u503c\u3001DCF\u3001\u5229\u6da6\u7387\u3001"
            "\u6bdb\u5229\u7387\u3001\u5355\u5e97\u3001\u56de\u672c\u7b49\u91d1\u878d\u5206\u6790\n"
            "- new_research_needed: \u6d89\u53ca\u6700\u65b0\u3001\u641c\u7d22\u3001\u4e0a\u7f51\u3001"
            "\u8865\u5145\u3001\u65b0\u95fb\u3001\u65b0\u8d44\u6599\u7b49\u9700\u8981\u8865\u5145\u7814\u7a76\n"
            "- report_generation_needed: \u6d89\u53ca\u62a5\u544a\u3001\u751f\u6210\u3001\u64b0\u5199\u3001"
            "\u603b\u7ed3\u7b49\u9700\u8981\u751f\u6210\u62a5\u544a\n"
            "- local_evidence_qa: \u5176\u4ed6\u57fa\u4e8e\u672c\u5730\u8bc1\u636e\u7684\u95ee\u7b54\n"
            "\u540c\u65f6\u63d0\u4f9b\u4e00\u4e2a\u6539\u8fdb\u7684\u641c\u7d22\u8bcd\uff0c"
            "\u7528\u4e8e\u8bc1\u636e\u5e93\u641c\u7d22\u3002\n"
            '\u8fd4\u56de JSON: {"intent": "...", "rewritten_query": "..."}'
        )
        user_prompt = f"\u95ee\u9898: {query}"
        result = self.llm_client.complete(
            system_prompt, user_prompt, context={"query": query}
        )
        intent, rewritten_query = _parse_triage_response(result.content, query)
        return {
            "query": query,
            "intent": intent,
            "rewritten_query": rewritten_query,
        }


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"

    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = _text(payload.get("query"))
        intent = _text(payload.get("intent")) or "local_evidence_qa"
        system_prompt = (
            "\u4f60\u662f\u7814\u7a76\u89c4\u5212\u5668\u3002\u6839\u636e\u7528\u6237\u95ee\u9898\u548c\u610f\u56fe\uff0c"
            "\u62c6\u89e3\u6210 3-5 \u4e2a\u5177\u4f53\u7814\u7a76\u4efb\u52a1\u3002\n"
            "\u6bcf\u4e2a\u4efb\u52a1\u5305\u542b title\uff08\u4efb\u52a1\u6807\u9898\uff09\u3001"
            "intent\uff08\u4efb\u52a1\u610f\u56fe\uff09\u3001query\uff08\u4efb\u52a1\u67e5\u8be2\u8bcd\uff09\u3002\n"
            '\u8fd4\u56de JSON: {"tasks": [{"title": "...", "intent": "...", "query": "..."}]}'
        )
        user_prompt = f"\u95ee\u9898: {query}\n\u610f\u56fe: {intent}"
        result = self.llm_client.complete(
            system_prompt, user_prompt, context={"query": query, "intent": intent}
        )
        tasks = _parse_planner_response(result.content, query, intent)
        return {"query": query, "intent": intent, "tasks": tasks}


class SearchAgent(BaseAgent):
    name = "SearchAgent"

    def __init__(self, search_tool: Any) -> None:
        self.search_tool = search_tool

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = _text(payload.get("query"))
        try:
            limit = _parse_positive_limit(payload.get("limit", 5))
        except ValueError as exc:
            return {"success": False, "results": [], "error": str(exc)}

        try:
            response = self.search_tool.run({"query": query, "limit": limit})
        except Exception as exc:
            return {"success": False, "results": [], "error": str(exc)}

        if not response.success:
            return {"success": False, "results": [], "error": response.error}

        data = dict(response.data)
        result = {
            "success": True,
            "results": data.get("results", []),
            "error": "",
            "data": data,
        }
        for key, value in data.items():
            result.setdefault(key, value)
        return result


class EvidenceExtractorAgent(BaseAgent):
    name = "EvidenceExtractorAgent"

    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        brand_id, brand_note = _safe_brand_id(payload.get("brand_id"))
        lens = _safe_lens(payload.get("lens"))
        source_results = payload.get("source_results", {})

        valid_items: list[dict[str, Any]] = []
        for item in _source_items(source_results):
            source_url = _first_text(item, "source_url", "url", "link")
            if not _is_http_url(source_url):
                continue
            snippet = _first_text(item, "claim", "snippet", "content", "excerpt", "summary")
            if not snippet:
                continue
            valid_items.append({"item": item, "url": source_url, "snippet": snippet})

        if not valid_items:
            return {"evidence": []}

        system_prompt = (
            "\u4f60\u662f\u8bc1\u636e\u62bd\u53d6\u5668\u3002\u4ece\u641c\u7d22\u7ed3\u679c\u7247\u6bb5\u4e2d"
            "\u62bd\u53d6\u6838\u5fc3\u8bba\u65ad\u3002\n"
            "\u4e3a\u6bcf\u6761\u641c\u7d22\u7ed3\u679c\u751f\u6210\u4e00\u4e2a claim\uff08\u4e00\u53e5\u8bdd\u6838\u5fc3\u8bba\u65ad\uff09\u3002\n"
            'source_type \u5fc5\u987b\u662f: news, company_site, prospectus, annual_report, industry_report\n'
            '\u8fd4\u56de JSON \u6570\u7ec4: '
            '[{"index": 0, "claim": "...", "source_type": "news", "confidence": 0.8}]\n'
            "index \u5bf9\u5e94\u8f93\u5165\u7684\u641c\u7d22\u7ed3\u679c\u5e8f\u53f7\uff080 \u5f00\u59cb\uff09"
        )
        snippets_text = "\n".join(
            f"[{i}] {vi['snippet']}" for i, vi in enumerate(valid_items)
        )
        user_prompt = (
            f"\u54c1\u724c: {brand_id}\n\u7ef4\u5ea6: {lens}\n"
            f"\u641c\u7d22\u7ed3\u679c:\n{snippets_text}"
        )
        result = self.llm_client.complete(
            system_prompt,
            user_prompt,
            context={"brand_id": brand_id, "lens": lens, "items": valid_items},
        )
        llm_claims = _parse_extractor_response(result.content)

        evidence: list[dict[str, Any]] = []
        for index, valid_item in enumerate(valid_items):
            item = valid_item["item"]
            llm_data = next(
                (c for c in llm_claims if c.get("index") == index), {}
            )
            claim = _text(llm_data.get("claim")) or valid_item["snippet"]
            source_type = _safe_source_type(
                llm_data.get("source_type")
                or _first_text(item, "source_type", "type")
            )
            confidence = _safe_confidence(llm_data.get("confidence", 0.5))

            title = _first_text(item, "source_title", "title", default="Untitled source")
            notes = _first_text(item, "notes", default="")
            if brand_note:
                notes = f"{notes} {brand_note}".strip()

            candidate = {
                "evidence_id": f"EV-CAND-{len(evidence) + 1:03d}",
                "brand_id": brand_id,
                "lens": lens,
                "claim": claim,
                "source_title": title,
                "source_url": valid_item["url"],
                "source_type": source_type,
                "source_date": _first_text(
                    item, "source_date", "date", default=DEFAULT_SOURCE_DATE
                ),
                "excerpt": valid_item["snippet"],
                "confidence": confidence,
                "review_status": "needs_review",
                "notes": notes,
            }
            try:
                validate_evidence_row(EvidenceRow(**candidate))
            except ValueError:
                continue
            evidence.append(candidate)

        return {"evidence": evidence}


class VerifierAgent(BaseAgent):
    name = "VerifierAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        evidence = dict(payload.get("evidence", {}))
        source_url = _text(evidence.get("source_url"))
        claim = _text(evidence.get("claim"))
        approved = bool(claim) and _is_http_url(source_url)
        evidence["review_status"] = "reviewed" if approved else "rejected"
        evidence["verification_status"] = "approved" if approved else "rejected"
        return evidence


class FinanceLensAgent(BaseAgent):
    name = "FinanceLensAgent"

    def __init__(self, finance_tool: Any) -> None:
        self.finance_tool = finance_tool

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response: ToolResponse = self.finance_tool.run(payload)
        except Exception as exc:
            return {
                "success": False,
                "assumptions": [],
                "scenarios": [],
                "error": str(exc),
            }

        if not response.success:
            return {
                "success": False,
                "assumptions": [],
                "scenarios": [],
                "error": response.error,
            }

        return {
            "success": True,
            "assumptions": response.data.get("assumptions", []),
            "scenarios": response.data.get("scenarios", []),
            "error": "",
        }


class WriterAgent(BaseAgent):
    name = "WriterAgent"

    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = _text(payload.get("query"))
        intent = _text(payload.get("intent")) or "local_evidence_qa"
        evidence = _valid_citable_evidence(payload.get("evidence", []))
        finance = payload.get("finance", {})
        if not isinstance(finance, dict):
            finance = {}

        evidence_ids = [_text(row.get("evidence_id")) for row in evidence]

        if not evidence:
            answer = (
                f"{ZH_EVIDENCE_INSUFFICIENT}: no reviewed citable evidence for {query}."
            )
            return {"answer": answer, "supporting_evidence_ids": []}

        system_prompt = (
            "\u4f60\u662f\u65b0\u8336\u996e\u54c1\u724c\u7814\u7a76\u5206\u6790\u5e08\u3002"
            "\u57fa\u4e8e\u8bc1\u636e\u751f\u6210\u4e2d\u6587\u7814\u7a76\u56de\u7b54\u3002\n"
            "\u8981\u6c42\uff1a\n"
            "1. \u56de\u7b54\u5fc5\u987b\u5f15\u7528 evidence ID\uff08\u5982 EV-001\uff09\n"
            "2. \u56de\u7b54\u5fc5\u987b\u5305\u542b\u201c\u5c40\u9650\u6027\u201d\u6bb5\u843d\uff0c"
            "\u8bf4\u660e\u8bc1\u636e\u7684\u4e0d\u8db3\n"
            "3. \u5982\u679c\u6709\u91d1\u878d\u5047\u8bbe\uff0c\u63d0\u53ca\u4f46\u4e0d\u6784\u6210"
            "\u6295\u8d44\u5efa\u8bae\n"
            "4. \u7528\u4e2d\u6587\u56de\u7b54\uff0c300\u5b57\u4ee5\u5185"
        )
        evidence_text = "\n".join(
            f"- {_text(row.get('evidence_id'))}: {_claim_or_excerpt(row)}"
            for row in evidence
        )
        finance_text = ""
        if finance.get("assumptions"):
            finance_text = (
                f"\n\u91d1\u878d\u5047\u8bbe: {len(finance['assumptions'])} \u6761\u5047\u8bbe\uff0c"
                f"\u542b DCF \u654f\u611f\u6027\u5206\u6790"
            )

        user_prompt = (
            f"\u95ee\u9898: {query}\n\u610f\u56fe: {intent}\n"
            f"\u8bc1\u636e:\n{evidence_text}{finance_text}"
        )
        result = self.llm_client.complete(
            system_prompt,
            user_prompt,
            context={"query": query, "evidence": evidence, "finance": finance},
        )
        answer = result.content

        for eid in evidence_ids:
            if eid and eid not in answer:
                answer += f" [{eid}]"

        if "\u5c40\u9650\u6027" not in answer:
            answer += (
                "\n\n\u5c40\u9650\u6027\uff1a\u4ee5\u4e0a\u7ed3\u8bba\u57fa\u4e8e\u73b0\u6709\u8bc1\u636e\uff0c"
                "\u53ef\u80fd\u672a\u5305\u542b\u6700\u65b0\u52a8\u6001\u3002"
            )

        if finance.get("assumptions"):
            if "FinanceLens" not in answer:
                answer += f"\n\nFinanceLens {ZH_SENSITIVITY}{ZH_SCENARIO_DISCUSSION}\uff1b"
            if ZH_NOT_INVESTMENT_ADVICE not in answer:
                answer += f"{ZH_NOT_INVESTMENT_ADVICE}\u3002"

        return {"answer": answer, "supporting_evidence_ids": evidence_ids}


def _task(title: str, intent: str, query: str) -> dict[str, str]:
    return {"title": title, "intent": intent, "query": query}


def _parse_triage_response(content: str, query: str) -> tuple[str, str]:
    """Parse LLM JSON response for TriageAgent. Falls back to rule-based
    routing on parse failure or invalid intent."""
    try:
        data = json.loads(content)
        intent = str(data.get("intent", "")).strip()
        rewritten_query = str(data.get("rewritten_query", query)).strip() or query
        valid_intents = {
            "finance_analysis_needed",
            "new_research_needed",
            "report_generation_needed",
            "local_evidence_qa",
        }
        if intent in valid_intents:
            return intent, rewritten_query
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    folded = query.casefold()
    if _contains_any(folded, FINANCE_TERMS):
        return "finance_analysis_needed", query
    if _contains_any(folded, RESEARCH_TERMS):
        return "new_research_needed", query
    if _contains_any(folded, REPORT_TERMS):
        return "report_generation_needed", query
    return "local_evidence_qa", query


def _parse_planner_response(
    content: str, query: str, intent: str
) -> list[dict[str, str]]:
    """Parse LLM JSON response for PlannerAgent. Falls back to rule-based
    task generation on parse failure."""
    try:
        data = json.loads(content)
        raw_tasks = data.get("tasks", [])
        if isinstance(raw_tasks, list) and raw_tasks:
            tasks: list[dict[str, str]] = []
            for raw in raw_tasks[:5]:
                if not isinstance(raw, dict):
                    continue
                title = _text(raw.get("title"))
                task_intent = _text(raw.get("intent")) or intent
                task_query = _text(raw.get("query")) or query
                if title:
                    tasks.append(
                        {"title": title, "intent": task_intent, "query": task_query}
                    )
            if tasks:
                return tasks
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return _rule_based_plan(query, intent)


def _rule_based_plan(query: str, intent: str) -> list[dict[str, str]]:
    """Rule-based fallback for PlannerAgent. Preserves the pre-LLM behavior."""
    folded = query.casefold()
    tasks: list[dict[str, str]] = []

    needs_search = intent == "new_research_needed" or _contains_any(
        folded, RESEARCH_TERMS
    )
    needs_finance = _contains_any(folded, FINANCE_ASSUMPTION_TERMS)
    needs_report = intent == "report_generation_needed"

    if needs_search:
        tasks.append(_task("Search new sources", "new_research_needed", query))

    tasks.append(_task("Review local evidence", "local_evidence_qa", query))

    if needs_finance:
        tasks.append(_task("Finance assumptions", "finance_analysis_needed", query))

    if needs_report:
        tasks.append(_task("Structure report", "report_generation_needed", query))

    if len(tasks) < 4:
        tasks.append(_task("Verify evidence", "local_evidence_qa", query))

    tasks = tasks[:4]
    tasks.append(_task("Draft final answer", intent, query))
    return tasks


def _parse_extractor_response(content: str) -> list[dict[str, Any]]:
    """Parse LLM JSON array response for EvidenceExtractorAgent. Returns
    empty list on parse failure (caller falls back to using raw snippets
    as claims)."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [
                item
                for item in data
                if isinstance(item, dict) and "claim" in item
            ]
        if isinstance(data, dict) and "evidence" in data:
            return [
                item
                for item in data["evidence"]
                if isinstance(item, dict) and "claim" in item
            ]
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.casefold() in text for term in terms)


def _parse_positive_limit(raw_limit: Any) -> int:
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be a positive integer") from exc
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    return limit


def _source_items(source_results: Any) -> list[dict[str, Any]]:
    if isinstance(source_results, list):
        return [item for item in source_results if isinstance(item, dict)]

    if not isinstance(source_results, dict):
        return []

    items: list[dict[str, Any]] = []
    for key in ("web", "results"):
        _extend_source_items(items, source_results.get(key))

    data = source_results.get("data")
    if isinstance(data, list):
        _extend_source_items(items, data)
    elif isinstance(data, dict):
        for key in ("web", "results", "items"):
            _extend_source_items(items, data.get(key))
    return items


def _extend_source_items(items: list[dict[str, Any]], value: Any) -> None:
    if isinstance(value, list):
        items.extend(item for item in value if isinstance(item, dict))


def _first_text(item: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = _text(item.get(key))
        if value:
            return value
    return default


def _safe_lens(raw_lens: Any) -> str:
    lens = _text(raw_lens)
    return lens if lens in ALLOWED_LENSES else DEFAULT_LENS


def _safe_brand_id(raw_brand_id: Any) -> tuple[str, str]:
    brand_id = _text(raw_brand_id)
    if brand_id in ALLOWED_BRANDS:
        return brand_id, ""
    return "luckin", "brand_id fallback to luckin."


def _safe_source_type(raw_source_type: Any) -> str:
    source_type = _text(raw_source_type)
    return source_type if source_type in ALLOWED_SOURCE_TYPES else DEFAULT_SOURCE_TYPE


def _safe_confidence(raw_confidence: Any) -> float:
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        return 0.5
    return min(max(confidence, 0.0), 1.0)


def _evidence_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        raw = raw.get("evidence", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _valid_citable_evidence(raw: Any) -> list[dict[str, Any]]:
    citable: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row in _evidence_list(raw):
        evidence_id = _text(row.get("evidence_id"))
        if not evidence_id or evidence_id in seen_ids:
            continue
        if _text(row.get("review_status")) != "reviewed":
            continue
        if not _claim_or_excerpt(row):
            continue
        if not _is_http_url(_text(row.get("source_url"))):
            continue
        citable.append(row)
        seen_ids.add(evidence_id)
    return citable


def _claim_or_excerpt(row: dict[str, Any]) -> str:
    return _text(row.get("claim")) or _text(row.get("excerpt"))


def _sentence_text(value: str) -> str:
    return _text(value).rstrip("\u3002.;\uff1b; ")


def _intent_label(intent: str) -> str:
    labels = {
        "finance_analysis_needed": "\u91d1\u878d\u5206\u6790",
        "new_research_needed": "\u8865\u5145\u7814\u7a76",
        "report_generation_needed": "\u62a5\u544a\u751f\u6210",
        "local_evidence_qa": "\u672c\u5730\u8bc1\u636e\u95ee\u7b54",
    }
    return labels.get(intent, intent)


def _is_http_url(value: str) -> bool:
    value = _text(value)
    if not value or any(character.isspace() for character in value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
