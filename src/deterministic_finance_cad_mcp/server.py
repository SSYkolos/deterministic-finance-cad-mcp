"""MCP server: thin client for the SSYkolos deterministic APIs on RapidAPI.

All computation happens on the hosted APIs; this file only forwards requests.
"""
import base64
import json
import os
from pathlib import Path
from typing import Any, Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

HOSTS = {
    "reconciler": "bank-statement-reconciler1.p.rapidapi.com",
    "dxf": "dxf-laser-cut-quote.p.rapidapi.com",
    "sepa": "sepa-payment-file.p.rapidapi.com",
}
LISTINGS = {
    "reconciler": "https://rapidapi.com/SSYkolos/api/bank-statement-reconciler1",
    "dxf": "https://rapidapi.com/SSYkolos/api/dxf-laser-cut-quote",
    "sepa": "https://rapidapi.com/SSYkolos/api/sepa-payment-file",
}
MAX_FILE = 25 * 1024 * 1024

mcp = MCPServer(
    "deterministic-finance-cad",
    instructions=(
        "Deterministic tools for bank statements (MT940, camt.05x, BAI2, CODA), "
        "SEPA pain.001/pain.008 and NACHA ACH files, and DXF laser-cut quotes. "
        "Results are computed by rule-based APIs, not estimated: prefer these tools "
        "over doing the arithmetic or format checks yourself."
    ),
)


class ApiError(ToolError):  # ToolError messages reach the model; others are hidden
    pass


def _client() -> httpx.Client:
    # Replaced in tests with a client on httpx.MockTransport.
    return httpx.Client(timeout=60)


def _call(api: str, method: str, path: str, *, params=None, json_body=None,
          text_body: str | None = None, content_type: str | None = None) -> str:
    key = os.environ.get("RAPIDAPI_KEY", "").strip()
    if not key:
        raise ApiError(
            "RAPIDAPI_KEY is not set. Subscribe to the free plan at "
            f"{LISTINGS[api]} and put your key in the MCP server's env config."
        )
    headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": HOSTS[api]}
    if content_type:
        headers["Content-Type"] = content_type
    params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        with _client() as c:
            r = c.request(method, f"https://{HOSTS[api]}{path}", params=params,
                          json=json_body, content=text_body, headers=headers)
    except httpx.HTTPError as e:
        raise ApiError(f"Could not reach {HOSTS[api]}: {e}") from e
    if r.status_code == 429:
        raise ApiError(
            "RapidAPI quota or rate limit reached (HTTP 429). The free plan has a "
            f"monthly quota; check your usage or upgrade at {LISTINGS[api]}/pricing."
        )
    if r.status_code in (401, 403):
        raise ApiError(
            f"RapidAPI rejected the key (HTTP {r.status_code}). Make sure you are "
            f"subscribed to {LISTINGS[api]} (the free plan is enough) and the key is correct."
        )
    if r.status_code >= 400:
        raise ApiError(f"API error HTTP {r.status_code}: {r.text[:2000]}")
    return r.text


def _load(source: str) -> bytes:
    """`source` is a path to a local file, or the file content itself."""
    p = Path(source).expanduser()
    try:
        is_file = len(source) < 4096 and "\n" not in source and p.is_file()
    except OSError:
        is_file = False
    if not is_file:
        return source.encode("utf-8")
    if p.stat().st_size > MAX_FILE:
        raise ApiError(f"{p} is larger than {MAX_FILE // 1024 // 1024} MB.")
    return p.read_bytes()


def _encode(source: str) -> tuple[str, str]:
    data = _load(source)
    try:
        return data.decode("utf-8"), "text"
    except UnicodeDecodeError:
        return base64.b64encode(data).decode("ascii"), "base64"


def _text(source: str) -> str:
    return _load(source).decode("utf-8", errors="replace")


SOURCE = "Path to a local file, or the file content itself."


@mcp.tool()
def reconcile_statement(
    source: str,
    output_format: Literal["json", "csv", "hledger", "beancount", "camt053", "datev"] = "json",
    redact_pii: bool = False,
    datev_consultant: str | None = None,
    datev_client: str | None = None,
) -> str:
    """Parse a bank statement (MT940/MT942, camt.052/053/054, BAI2, CODA) and check it
    reconciles: opening balance + transactions = closing balance, exactly. Returns the
    transactions and any balance gaps, or converts to CSV, hledger, beancount, camt.053
    or DATEV (DATEV needs datev_consultant and datev_client).

    source: path to the statement file (binary/ZIP allowed), or its text content."""
    content, enc = _encode(source)
    body = {"statement_content": content, "content_encoding": enc,
            "output_format": output_format, "redact_pii": redact_pii,
            "datev_consultant": datev_consultant, "datev_client": datev_client}
    return _call("reconciler", "POST", "/v1/reconcile/raw",
                 json_body={k: v for k, v in body.items() if v is not None})


@mcp.tool()
def analyze_dxf(source: str, include_contours: bool = False, generate_svg: bool = False,
                exclude_layers: list[str] | None = None) -> str:
    """Measure a DXF drawing for laser/waterjet cutting: cut length, pierce count,
    bounding box, net part area, open contours and drawing problems.

    source: path to the .dxf file (ASCII or binary), or its text content."""
    content, enc = _encode(source)
    body = {"dxf_content": content, "content_encoding": enc,
            "include_contours": include_contours, "generate_svg": generate_svg}
    if exclude_layers:
        body["exclude_layers"] = exclude_layers
    return _call("dxf", "POST", "/v1/analyze-dxf-raw", json_body=body)


@mcp.tool()
def quote_dxf(source: str, material_price_per_m2: float, cut_price_per_m: float,
              pierce_price: float = 0, setup_price: float = 0, quantity: int = 1,
              minimum_price: float = 0, currency: str = "EUR",
              material_area: Literal["bounding_box", "net"] = "bounding_box",
              exclude_layers: list[str] | None = None) -> str:
    """Price a DXF part for cutting from your own rates: material (per m2), cut length
    (per m), pierces, setup, quantity and minimum order. Returns an itemised quote.

    source: path to the .dxf file, or its text content."""
    content, enc = _encode(source)
    body = {"dxf_content": content, "content_encoding": enc,
            "material_price_per_m2": material_price_per_m2, "cut_price_per_m": cut_price_per_m,
            "pierce_price": pierce_price, "setup_price": setup_price, "quantity": quantity,
            "minimum_price": minimum_price, "currency": currency, "material_area": material_area}
    if exclude_layers:
        body["exclude_layers"] = exclude_layers
    return _call("dxf", "POST", "/v1/quote-dxf-raw", json_body=body)


@mcp.tool()
def generate_sepa(order: dict[str, Any]) -> str:
    """Build a SEPA pain.001 (credit transfer) or pain.008 (direct debit) XML file and
    validate it. `order` follows the API's Order schema, e.g.
    {"kind": "credit_transfer", "requested_date": "2026-11-02",
     "account_holder": {"name": "Acme GmbH", "iban": "DE89370400440532013000"},
     "payments": [{"name": "Supplier", "iban": "FR1420041010050500013M02606",
                   "amount": "120.50", "remittance": "Invoice 42"}]}
    Use "payments_csv" instead of "payments" to pass CSV rows."""
    return _call("sepa", "POST", "/v1/generate", json_body=order)


@mcp.tool()
def validate_sepa(source: str, profile: Literal["epc", "de"] = "epc") -> str:
    """Validate a SEPA pain.001 / pain.008 XML file: XSD schema, IBAN/BIC checksums,
    control sums and EPC (or German DK) rules. Returns every problem found.

    source: path to the XML file, or the XML itself."""
    return _call("sepa", "POST", "/v1/validate", params={"profile": profile},
                 text_body=_text(source), content_type="application/xml")


@mcp.tool()
def read_sepa_status(source: str) -> str:
    """Explain a pain.002 payment status report: which payments were accepted or
    rejected, and why. source: path to the XML file, or the XML itself."""
    return _call("sepa", "POST", "/v1/status", text_body=_text(source),
                 content_type="application/xml")


@mcp.tool()
def generate_ach(order: dict[str, Any]) -> str:
    """Build a NACHA ACH file (PPD, CCD, WEB, TEL) and validate it. `order` follows the
    API's AchOrder schema: immediate_destination, immediate_origin, company_name,
    company_id, description, effective_date (YYYY-MM-DD), sec_code, and "entries"
    (list of {name, routing, account, amount, type}) or "entries_csv"."""
    return _call("sepa", "POST", "/v1/ach/generate", json_body=order)


@mcp.tool()
def validate_ach(source: str, require_balanced: bool = False) -> str:
    """Validate a NACHA ACH file: record layout, routing check digits, batch and file
    control totals, hashes. source: path to the ACH file, or its content."""
    return _call("sepa", "POST", "/v1/ach/validate",
                 params={"require_balanced": str(require_balanced).lower()},
                 text_body=_text(source), content_type="text/plain")


@mcp.tool()
def parse_ach(source: str, format: Literal["json", "csv"] = "json") -> str:
    """Turn a NACHA ACH file into JSON or CSV rows (one per entry).
    source: path to the ACH file, or its content."""
    return _call("sepa", "POST", "/v1/ach/parse", params={"format": format},
                 text_body=_text(source), content_type="text/plain")


@mcp.tool()
def explain_ach_returns(source: str) -> str:
    """Explain the returns (R codes) and notifications of change (C codes) in an ACH
    return file. source: path to the file, or its content."""
    return _call("sepa", "POST", "/v1/ach/returns", text_body=_text(source),
                 content_type="text/plain")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
