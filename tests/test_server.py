import json
import os

import httpx
import pytest

from deterministic_finance_cad_mcp import server as s


class Seen(list):
    pass


@pytest.fixture
def api(monkeypatch):
    """Mock the HTTP layer; returns the list of captured requests."""
    seen, reply = Seen(), {"status": 200, "body": '{"ok": true}'}

    def handler(req):
        seen.append(req)
        return httpx.Response(reply["status"], text=reply["body"])

    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    monkeypatch.setattr(s, "_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    seen.reply = reply
    return seen



def test_reconcile_text_content(api):
    assert s.reconcile_statement(":20:REF\n:60F:C261001EUR100,00\n") == '{"ok": true}'
    r = api[0]
    assert r.url.host == "bank-statement-reconciler1.p.rapidapi.com"
    assert r.url.path == "/v1/reconcile/raw"
    assert r.headers["x-rapidapi-key"] == "test-key"
    assert r.headers["x-rapidapi-host"] == "bank-statement-reconciler1.p.rapidapi.com"
    body = json.loads(r.content)
    assert body["content_encoding"] == "text" and body["output_format"] == "json"
    assert "datev_client" not in body


def test_binary_file_is_base64(api, tmp_path):
    f = tmp_path / "a.zip"
    f.write_bytes(b"PK\x03\x04\xff\xfe")
    s.analyze_dxf(str(f))
    body = json.loads(api[0].content)
    assert api[0].url.path == "/v1/analyze-dxf-raw"
    assert body["content_encoding"] == "base64" and body["dxf_content"] == "UEsDBP/+"


def test_quote_params(api):
    s.quote_dxf("0\nSECTION\n0\nEOF\n", material_price_per_m2=40, cut_price_per_m=1.2, quantity=5)
    body = json.loads(api[0].content)
    assert api[0].url.host == "dxf-laser-cut-quote.p.rapidapi.com"
    assert body["quantity"] == 5 and body["material_area"] == "bounding_box"


def test_validate_sepa_sends_xml_file(api, tmp_path):
    f = tmp_path / "p.xml"
    f.write_text("<Document/>")
    s.validate_sepa(str(f), profile="de")
    r = api[0]
    assert r.url.host == "sepa-payment-file.p.rapidapi.com"
    assert r.url.path == "/v1/validate" and r.url.params["profile"] == "de"
    assert r.headers["content-type"] == "application/xml" and r.content == b"<Document/>"


def test_ach_endpoints(api):
    s.validate_ach("101 ...", require_balanced=True)
    s.parse_ach("101 ...", format="csv")
    s.explain_ach_returns("101 ...")
    s.generate_ach({"company_name": "X"})
    s.generate_sepa({"kind": "credit_transfer"})
    s.read_sepa_status("<Document/>")
    paths = [r.url.path for r in api]
    assert paths == ["/v1/ach/validate", "/v1/ach/parse", "/v1/ach/returns",
                     "/v1/ach/generate", "/v1/generate", "/v1/status"]
    assert api[0].url.params["require_balanced"] == "true"
    assert json.loads(api[3].content) == {"company_name": "X"}


def test_429_quota_message(api):
    api.reply.update(status=429, body="Too many")
    with pytest.raises(s.ApiError, match="quota"):
        s.validate_ach("x")


def test_403_and_500(api):
    api.reply.update(status=403, body="")
    with pytest.raises(s.ApiError, match="subscribed"):
        s.validate_ach("x")
    api.reply.update(status=422, body='{"detail":"bad"}')
    with pytest.raises(s.ApiError, match="422.*bad"):
        s.validate_ach("x")


def test_missing_key(monkeypatch):
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    with pytest.raises(s.ApiError, match="RAPIDAPI_KEY"):
        s.validate_ach("x")


async def _list_tools():
    return [t.name for t in await s.mcp.list_tools()]


def test_tools_registered():
    import asyncio
    names = asyncio.run(_list_tools())
    assert {"reconcile_statement", "analyze_dxf", "quote_dxf", "validate_sepa",
            "generate_sepa", "validate_ach"} <= set(names)


@pytest.mark.skipif(not os.environ.get("RAPIDAPI_KEY"), reason="needs a real RAPIDAPI_KEY")
def test_smoke_real_api():
    mt940 = (":20:STMT1\n:25:DE89370400440532013000\n:28C:1/1\n:60F:C261001EUR100,00\n"
             ":61:2610011001C50,00NTRFNONREF\n:86:Test\n:62F:C261001EUR150,00\n-")
    out = json.loads(s.reconcile_statement(mt940))
    assert out
