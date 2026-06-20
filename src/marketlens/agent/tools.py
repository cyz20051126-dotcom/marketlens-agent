from __future__ import annotations

import csv
import hashlib
import html as html_module
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from marketlens.agent.runtime import ToolResponse
from marketlens.schemas import EvidenceRow, validate_evidence_row


EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "brand_id",
    "lens",
    "claim",
    "source_title",
    "source_url",
    "source_type",
    "source_date",
    "excerpt",
    "confidence",
    "review_status",
    "notes",
]

REQUIRED_EVIDENCE_FIELDS = [
    "evidence_id",
    "brand_id",
    "lens",
    "claim",
    "source_title",
    "source_url",
    "source_type",
    "source_date",
    "excerpt",
    "confidence",
    "review_status",
]


def _row_to_dict(row: EvidenceRow) -> dict[str, Any]:
    return row.to_dict()


def _evidence_from_dict(raw: dict[str, Any]) -> EvidenceRow:
    for field_name in REQUIRED_EVIDENCE_FIELDS:
        if field_name not in raw:
            raise ValueError(f"{field_name} is required")
        value = raw[field_name]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{field_name} is required")

    try:
        confidence = float(raw["confidence"])
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be numeric") from exc

    return EvidenceRow(
        evidence_id=raw["evidence_id"],
        brand_id=raw["brand_id"],
        lens=raw["lens"],
        claim=raw["claim"],
        source_title=raw["source_title"],
        source_url=raw["source_url"],
        source_type=raw["source_type"],
        source_date=raw["source_date"],
        excerpt=raw["excerpt"],
        confidence=confidence,
        review_status=raw["review_status"],
        notes="" if raw.get("notes") is None else str(raw.get("notes", "")),
    )


def _existing_evidence_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return {str(row.get("evidence_id", "")) for row in reader}


def _parse_limit(raw_limit: Any) -> int:
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be a positive integer") from exc

    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    return limit


def _resolve_inside_root(source_root: Path, requested_path: Any) -> Path:
    raw_path = Path(str(requested_path))
    candidate = raw_path if raw_path.is_absolute() else source_root / raw_path
    resolved = candidate.resolve()
    root = source_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("source_path must resolve inside source_root") from exc
    return resolved


class EvidenceSearchTool:
    name = "EvidenceSearchTool"
    description = "Search reviewed local evidence by query, brand, and lens."

    def __init__(self, rows: list[EvidenceRow]) -> None:
        self.rows = list(rows)

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        query = str(payload.get("query", "") or "").strip()
        brand_id = str(payload.get("brand_id", "") or "").strip().casefold()
        lens = str(payload.get("lens", "") or "").strip().casefold()
        try:
            limit = _parse_limit(payload.get("limit", 5))
        except ValueError as exc:
            return ToolResponse(False, {}, str(exc))
        allow_broad_fallback = payload.get("allow_broad_fallback") is True

        filtered = [row for row in self.rows if row.review_status == "reviewed"]
        if brand_id:
            filtered = [row for row in filtered if row.brand_id.casefold() == brand_id]
        if lens:
            filtered = [row for row in filtered if row.lens.casefold() == lens]

        matched = filtered
        if query:
            needle = query.casefold()
            matched = [
                row
                for row in filtered
                if needle
                in " ".join(
                    [row.claim, row.excerpt, row.source_title, row.notes]
                ).casefold()
            ]

            if not matched and allow_broad_fallback and (brand_id or lens):
                matched = sorted(filtered, key=lambda row: row.confidence, reverse=True)

        selected = sorted(matched, key=lambda row: row.confidence, reverse=True)[:limit]
        evidence = [_row_to_dict(row) for row in selected]
        return ToolResponse(
            success=True,
            data={"evidence": evidence, "count": len(evidence), "query": query},
        )


class SourceReadTool:
    name = "SourceReadTool"
    description = "Read one evidence row or a source artifact text file."

    def __init__(
        self, rows: list[EvidenceRow], source_root: Path | None = None
    ) -> None:
        self.rows = list(rows)
        self.source_root = Path(source_root).resolve() if source_root is not None else None

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        evidence_id = str(payload.get("evidence_id", "") or "").strip()
        if evidence_id:
            for row in self.rows:
                if row.evidence_id == evidence_id:
                    return ToolResponse(True, {"evidence": _row_to_dict(row)})
            return ToolResponse(False, {}, f"Evidence not found: {evidence_id}")

        requested_path = payload.get("source_path") or payload.get("artifact_path")
        if requested_path:
            if self.source_root is None:
                return ToolResponse(False, {}, "source_root is required to read source files")
            try:
                resolved_path = _resolve_inside_root(self.source_root, requested_path)
            except ValueError as exc:
                return ToolResponse(False, {}, str(exc))
            if not resolved_path.is_file():
                return ToolResponse(False, {}, f"Source file not found: {requested_path}")

            content = resolved_path.read_text(encoding="utf-8")
            return ToolResponse(
                True,
                {
                    "source_path": str(resolved_path),
                    "content": content,
                    "content_length": len(content),
                },
            )

        return ToolResponse(False, {}, "evidence_id, source_path, or artifact_path is required")


class EvidenceStoreTool:
    name = "EvidenceStoreTool"
    description = "Validate and append evidence rows to a CSV store."

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        raw = payload.get("evidence", {})
        if not isinstance(raw, dict):
            return ToolResponse(False, {}, "evidence must be a dictionary")

        try:
            row = _evidence_from_dict(raw)
            validate_evidence_row(row)
        except Exception as exc:
            return ToolResponse(False, {}, str(exc))

        existing_ids = _existing_evidence_ids(self.path)
        if row.evidence_id in existing_ids:
            return ToolResponse(False, {}, f"Duplicate evidence_id: {row.evidence_id}")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=EVIDENCE_FIELDNAMES)
            if write_header:
                writer.writeheader()
            writer.writerow(_row_to_dict(row))

        return ToolResponse(True, {"stored_evidence_id": row.evidence_id})


class WebSearchTool:
    """Search the web via DuckDuckGo HTML endpoint. Free, no API key, no
    quota. Parses result anchors and snippets with regex over the HTML.
    Falls back to an empty result set on network failure so the orchestrator
    can proceed with local evidence."""

    name = "WebSearchTool"
    description = "Search the web via DuckDuckGo and return title/url/snippet."

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = Path(output_dir) if output_dir else None

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        query = str(payload.get("query", "") or "").strip()
        try:
            limit = _parse_limit(payload.get("limit", 5))
        except ValueError as exc:
            return ToolResponse(False, {"results": []}, str(exc))

        if not query:
            return ToolResponse(False, {"results": []}, "query must not be empty")

        try:
            results = _search_duckduckgo(query, limit)
        except Exception as exc:
            return ToolResponse(
                False,
                {"results": [], "query": query, "status": "degraded_fallback"},
                f"DuckDuckGo search failed: {exc}",
            )

        if self.output_dir is not None:
            self._write_artifact(query, results)

        return ToolResponse(
            True,
            {"results": results, "query": query, "status": "live", "count": len(results)},
        )

    def _write_artifact(self, query: str, results: list[dict[str, str]]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", query.strip()).strip("-").lower()
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
        filename = f"web-search-{slug or 'request'}-{query_hash}.json"
        artifact_path = self.output_dir / filename
        artifact = {
            "tool": self.name,
            "provider": "duckduckgo",
            "query": query,
            "result_count": len(results),
            "results": results,
        }
        artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# Backward-compatible alias so existing imports keep working during the
# migration. New code should use WebSearchTool.
FirecrawlSearchTool = WebSearchTool


# --- DuckDuckGo search helpers --------------------------------------------

_DDG_RESULT_PATTERN = re.compile(
    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
    r'.*?<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
    re.DOTALL,
)
_TAG_PATTERN = re.compile(r"<[^>]+>")


def _search_duckduckgo(query: str, limit: int) -> list[dict[str, str]]:
    """Call DuckDuckGo HTML endpoint and parse results. Raises on network
    error so the caller (WebSearchTool.run) can catch and degrade."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MarketLensAgent/1.0 (research demo)",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return _parse_duckduckgo_html(raw, limit)


def _parse_duckduckgo_html(html: str, limit: int) -> list[dict[str, str]]:
    """Extract title/url/snippet from DuckDuckGo HTML results page."""
    results: list[dict[str, str]] = []
    for match in _DDG_RESULT_PATTERN.finditer(html):
        href = match.group(1)
        title = _strip_tags(html_module.unescape(match.group(2))).strip()
        snippet = _strip_tags(html_module.unescape(match.group(3))).strip()
        url = _extract_ddg_target_url(href)
        if title and url:
            results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= limit:
            break
    return results


def _strip_tags(text: str) -> str:
    return _TAG_PATTERN.sub("", text)


def _extract_ddg_target_url(href: str) -> str:
    """DuckDuckGo wraps result URLs in a redirect like
    //duckduckgo.com/l/?uddg=ENCODED_URL&rut=... — extract the real URL."""
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    parsed = urllib.parse.urlparse(href)
    query_params = urllib.parse.parse_qs(parsed.query)
    target = query_params.get("uddg", [None])[0]
    if target:
        return urllib.parse.unquote(target)
    return href

