"""dist/server.mcpb -> dist/smithery.mcpb with each tool's inputSchema in manifest.json.

Smithery requires inputSchema per tool; the MCPB manifest schema forbids it, so only the
Smithery copy gets it. Run after `npx @anthropic-ai/mcpb pack . dist/server.mcpb`.
"""
import asyncio
import json
import zipfile

from deterministic_finance_cad_mcp.server import mcp

tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
manifest = json.load(open("manifest.json", encoding="utf-8"))
for t in manifest["tools"]:
    t["inputSchema"] = tools[t["name"]].input_schema

with zipfile.ZipFile("dist/server.mcpb") as src, \
        zipfile.ZipFile("dist/smithery.mcpb", "w", zipfile.ZIP_DEFLATED) as out:
    for item in src.infolist():
        data = src.read(item.filename)
        if item.filename == "manifest.json":
            data = json.dumps(manifest, indent=2).encode()
        out.writestr(item, data)
print("wrote dist/smithery.mcpb")
