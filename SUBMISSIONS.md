# Directory submissions

Ready-to-paste texts. Each site is submitted by the repo owner (SSYkolos).

**Repository:** https://github.com/SSYkolos/deterministic-finance-cad-mcp
**Name:** Deterministic Finance & CAD
**Category:** Finance
**Short description (≤ 160 chars):**
Exact tools for AI agents: reconcile bank statements (MT940, camt, BAI2, CODA), build and validate SEPA and NACHA ACH files, price DXF parts for laser cutting.

**Long description:**
Language models guess at arithmetic and strict file formats. This MCP server gives the
assistant rule-based tools instead: parse and reconcile bank statements and convert them
to CSV, hledger, beancount, camt.053 or DATEV; generate and validate SEPA pain.001 /
pain.008 files and read pain.002 reports; generate, validate and parse NACHA ACH files
and explain return codes; measure DXF drawings (cut length, pierces, area, open
contours) and produce itemised laser-cut quotes. Same input, same output, every time.
Local stdio server (Python); needs a free RapidAPI key.

**Tags:** bank-statement, mt940, camt053, bai2, sepa, nacha, ach, dxf, laser-cutting, reconciliation, accounting, datev

---

## 1. glama.ai

Glama also indexes public GitHub MCP repos on its own; submitting makes it faster and
lets you claim it (`glama.json` in the repo lists SSYkolos as maintainer).

1. Go to https://glama.ai/mcp/servers and click **Add Server**.
2. Sign up / sign in (GitHub login is easiest).
3. Paste the repository URL and submit.
4. After it is listed, open the server page and **Claim** it (proves ownership through
   GitHub). Glama builds the `Dockerfile` to check the server starts and lists tools.

## 2. smithery.ai

Smithery lists local (stdio) servers as an **MCPB bundle**.

1. Build the bundle (in the repo folder):
   `npx -y @anthropic-ai/mcpb pack . dist/server.mcpb`
   (or download `server.mcpb` from the GitHub release, if attached).
2. Go to https://smithery.ai/new and sign in with GitHub.
3. Choose **Local (MCPB Bundle)**, upload `server.mcpb`, and complete the form with the
   texts above. The RapidAPI key is a `user_config` field marked sensitive, so Smithery
   asks each user for their own key.

## 3. mcpservers.org

Free listing, reviewed within about 2 weeks (a $39 premium option exists; not needed).

1. Go to https://mcpservers.org/submit
2. Fill in:
   - **Server Name:** Deterministic Finance & CAD
   - **Category:** Finance
   - **Short Description:** the short description above
   - **Repository:** the repository URL
   - **Official MCP Registry Name:** leave empty
   - **Supports remote connections:** leave unchecked (it is a local stdio server)
   - **Contact Email:** your support e-mail
   - **Plan:** Free
3. Submit.
