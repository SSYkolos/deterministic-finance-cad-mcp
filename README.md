# Deterministic Finance & CAD MCP

An [MCP](https://modelcontextprotocol.io) server that gives Claude, Cursor and other AI
assistants exact, rule-based tools for:

- **Bank statements**: parse MT940/MT942, camt.052/053/054, BAI2 and CODA, check that
  opening balance + transactions = closing balance, convert to CSV, hledger, beancount,
  camt.053 or DATEV.
- **SEPA payment files**: generate and validate pain.001 / pain.008 XML (XSD, IBAN/BIC
  checksums, control sums, EPC and German DK rules), read pain.002 status reports.
- **NACHA ACH files**: generate, validate and parse ACH files, explain return (R) and
  notification-of-change (C) codes.
- **DXF laser-cut quotes**: measure cut length, pierces, part area and drawing problems,
  then price a part from your own rates.

This repository is only a thin client. The work is done by hosted APIs on
[RapidAPI](https://rapidapi.com/user/SSYkolos); the server forwards your request and
returns the API's answer.

## Why deterministic tools?

Language models are good at reading a request and bad at exact arithmetic and strict
formats. Ask a model to sum 400 transactions, check an IBAN checksum or measure the cut
length of a DXF and it will produce a plausible number that may be wrong. These tools
compute the answer with fixed rules: the same input always gives the same output, and
errors are reported, not guessed around. The assistant decides *what* to do; the tool
does the counting.

## Tools

| Tool | What it does |
|---|---|
| `reconcile_statement` | Parse and reconcile a bank statement; optional CSV / hledger / beancount / camt.053 / DATEV output |
| `analyze_dxf` | Cut length, pierces, bounding box, area, open contours of a DXF |
| `quote_dxf` | Itemised cutting quote from material, cut, pierce and setup rates |
| `generate_sepa` | Build and validate a pain.001 / pain.008 file from JSON or CSV |
| `validate_sepa` | Validate a pain.001 / pain.008 file |
| `read_sepa_status` | Explain a pain.002 status report |
| `generate_ach` | Build and validate a NACHA ACH file |
| `validate_ach` | Validate a NACHA ACH file |
| `parse_ach` | ACH file to JSON or CSV rows |
| `explain_ach_returns` | Explain R and C codes in an ACH return file |

File tools take `source`: a path to a local file, or the file content itself.

## 1. Get a free RapidAPI key

1. Create a free account at [rapidapi.com](https://rapidapi.com).
2. Open the APIs you want and subscribe to the **free** plan:
   - [Bank Statement Reconciler](https://rapidapi.com/SSYkolos/api/bank-statement-reconciler1)
   - [DXF Laser Cut Quote](https://rapidapi.com/SSYkolos/api/dxf-laser-cut-quote)
   - [SEPA Payment File (incl. NACHA ACH)](https://rapidapi.com/SSYkolos/api/sepa-payment-file)
3. Copy your key (`X-RapidAPI-Key`) from any endpoint page. One key works for all three.

The free plans have a monthly quota. When it runs out the tools return a clear
"quota reached" message instead of failing silently.

## 2. Install

Needs Python 3.10+. With [uv](https://docs.astral.sh/uv/) you don't need to install
anything by hand; `uvx` runs the server straight from this repository.

```bash
uvx --from git+https://github.com/SSYkolos/deterministic-finance-cad-mcp deterministic-finance-cad-mcp
```

Or with pip:

```bash
pip install git+https://github.com/SSYkolos/deterministic-finance-cad-mcp
```

## 3. Configure your assistant

### Claude Desktop

Edit `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "deterministic-finance-cad": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/SSYkolos/deterministic-finance-cad-mcp", "deterministic-finance-cad-mcp"],
      "env": { "RAPIDAPI_KEY": "your-rapidapi-key" }
    }
  }
}
```

Restart Claude Desktop. If you installed with pip, use
`"command": "deterministic-finance-cad-mcp"` and drop `args`.

### Cursor

Add the same block to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project).

### Claude Code

```bash
claude mcp add deterministic-finance-cad -e RAPIDAPI_KEY=your-rapidapi-key -- uvx --from git+https://github.com/SSYkolos/deterministic-finance-cad-mcp deterministic-finance-cad-mcp
```

Then ask, for example: *"Reconcile ~/Downloads/statement.sta and list any balance gaps"*
or *"Quote part.dxf in 3 mm steel: 45 EUR/m², 1.10 EUR per metre cut, 0.15 per pierce, 20 pieces"*.

## Privacy

Files you pass to a tool are sent to the API over HTTPS for processing. For how
data is handled, see [ssykolos.github.io](https://ssykolos.github.io).

## Development

```bash
pip install -e ".[test]"
pytest
```

Tests mock the HTTP layer. `test_smoke_real_api` calls the live reconciler and runs only
when `RAPIDAPI_KEY` is set.

## More

Docs, demos and direct (non-RapidAPI) plans: **[ssykolos.github.io](https://ssykolos.github.io)**

MIT licensed.
