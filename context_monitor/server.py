# Context Monitor MCP Server
# Real-time token dashboard for Claude Code sessions.
# Reads JSONL session logs, counts tokens with tiktoken, categorizes by source.
#
# Tools:
#   context_check      — quick health: cumulative cost + current window estimate
#   context_top_sources — ranked token consumers in current window
#   context_suggest    — what can be unloaded or compressed
#   context_history    — cumulative token growth over session timeline

import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from context_monitor import TokenCounter, SourceCategorizer, SuggestionEngine
server = Server("context-monitor")
counter = TokenCounter()
categorizer = SourceCategorizer()
suggestor = SuggestionEngine()

SESSION_LOG_DIR = os.path.expanduser("~/.claude/projects")
CONTEXT_LIMIT = 200000


def find_latest_session(projects_dir: str) -> Path | None:
    base = Path(projects_dir)
    if not base.exists():
        return None
    jsonl_files = sorted(base.rglob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonl_files[0] if jsonl_files else None


def parse_jsonl_session(path: Path) -> list[dict]:
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return messages


def _extract_text(msg: dict) -> str:
    message = msg.get("message", {})
    content = message.get("content", [])
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


def compute_session_stats(messages: list[dict]) -> dict[str, Any]:
    total = 0
    categories: dict[str, int] = {}
    sources: list[dict] = []

    for msg in messages:
        text = _extract_text(msg)
        n = counter.count(text)
        cat = categorizer.classify(msg, text)
        categories[cat] = categories.get(cat, 0) + n
        total += n
        if n > 500:
            sources.append({"category": cat, "tokens": n, "preview": text[:120]})

    sources.sort(key=lambda x: x["tokens"], reverse=True)
    return {"cumulative_total": total, "categories": categories, "top_sources": sources[:15]}


def estimate_current_context(messages: list[dict], limit: int = 200000) -> dict[str, Any]:
    window_msgs = []
    window_tokens = 0
    for msg in reversed(messages):
        text = _extract_text(msg)
        n = counter.count(text)
        if window_tokens + n > limit:
            break
        window_msgs.append(msg)
        window_tokens += n
    window_msgs.reverse()

    categories: dict[str, int] = {}
    for msg in window_msgs:
        text = _extract_text(msg)
        cat = categorizer.classify(msg, text)
        categories[cat] = categories.get(cat, 0) + counter.count(text)

    return {
        "estimated_tokens": window_tokens,
        "limit": limit,
        "usage_pct": round(window_tokens / limit * 100, 1),
        "messages_in_window": len(window_msgs),
        "categories": categories,
    }


def health_level(pct: float) -> str:
    if pct < 60:
        return "green"
    elif pct < 80:
        return "yellow"
    elif pct < 90:
        return "red"
    return "critical"


# --- Tool implementations ---

async def do_context_check() -> str:
    session_path = find_latest_session(SESSION_LOG_DIR)
    if not session_path:
        return json.dumps({"error": "No session JSONL found"}, ensure_ascii=False)

    msgs = parse_jsonl_session(session_path)
    cumulative = compute_session_stats(msgs)
    current = estimate_current_context(msgs)
    suggestions = suggestor.generate(current, msgs)

    top_cats = sorted(current["categories"].items(), key=lambda x: x[1], reverse=True)

    return json.dumps({
        "session": str(session_path),
        "cumulative": {
            "total_tokens": cumulative["cumulative_total"],
            "note": "Full session cost — includes repeated system injections each turn",
        },
        "current_window": {
            "estimated_tokens": current["estimated_tokens"],
            "limit": current["limit"],
            "usage_pct": current["usage_pct"],
            "health": health_level(current["usage_pct"]),
            "messages_in_window": current["messages_in_window"],
            "categories": {k: v for k, v in top_cats},
            "top_3": [
                {"category": c[0], "tokens": c[1],
                 "pct": round(c[1] / max(current["estimated_tokens"], 1) * 100, 1)}
                for c in top_cats[:3]
            ],
        },
        "suggestions": suggestions[:3],
    }, ensure_ascii=False, indent=2)


async def do_context_top_sources(top_n: int, category: str) -> str:
    session_path = find_latest_session(SESSION_LOG_DIR)
    if not session_path:
        return json.dumps({"error": "No session JSONL found"}, ensure_ascii=False)

    msgs = parse_jsonl_session(session_path)
    current = estimate_current_context(msgs)

    sources: list[dict] = []
    start = max(0, len(msgs) - current["messages_in_window"])
    for msg in msgs[start:]:
        text = _extract_text(msg)
        n = counter.count(text)
        cat = categorizer.classify(msg, text)
        if not category or cat == category:
            sources.append({"category": cat, "tokens": n, "preview": text[:120]})

    sources.sort(key=lambda x: x["tokens"], reverse=True)
    sources = sources[:top_n]

    return json.dumps({
        "window_tokens": current["estimated_tokens"],
        "limit": current["limit"],
        "usage_pct": current["usage_pct"],
        "category_filter": category or "all",
        "sources": [
            {"rank": i + 1, "category": s["category"],
             "tokens": s["tokens"],
             "pct": round(s["tokens"] / max(current["estimated_tokens"], 1) * 100, 1),
             "preview": s["preview"]}
            for i, s in enumerate(sources)
        ],
    }, ensure_ascii=False, indent=2)


async def do_context_suggest() -> str:
    session_path = find_latest_session(SESSION_LOG_DIR)
    if not session_path:
        return json.dumps({"error": "No session JSONL found"}, ensure_ascii=False)

    msgs = parse_jsonl_session(session_path)
    current = estimate_current_context(msgs)
    suggestions = suggestor.generate(current, msgs)
    total_savable = sum(s.get("tokens_freed", 0) for s in suggestions)

    return json.dumps({
        "current_window_tokens": current["estimated_tokens"],
        "usage_pct": current["usage_pct"],
        "suggestions": suggestions,
        "total_savable": total_savable,
        "after_optimization_pct": round(
            max(current["estimated_tokens"] - total_savable, 0) / current["limit"] * 100, 1
        ),
    }, ensure_ascii=False, indent=2)


async def do_context_history() -> str:
    session_path = find_latest_session(SESSION_LOG_DIR)
    if not session_path:
        return json.dumps({"error": "No session JSONL found"}, ensure_ascii=False)

    msgs = parse_jsonl_session(session_path)
    total_msgs = len(msgs)
    interval = max(1, total_msgs // 8)
    snapshots = []
    running_total = 0

    for i in range(total_msgs):
        running_total += counter.count(_extract_text(msgs[i]))
        if i % interval == 0 or i == total_msgs - 1:
            snapshots.append({
                "message_index": i + 1,
                "cumulative_tokens": running_total,
                "session_timeline_pct": round((i + 1) / total_msgs * 100, 1),
            })

    current = estimate_current_context(msgs)

    return json.dumps({
        "total_messages": total_msgs,
        "session_cumulative_tokens": running_total,
        "current_window_tokens": current["estimated_tokens"],
        "current_window_pct": current["usage_pct"],
        "snapshots": snapshots,
    }, ensure_ascii=False, indent=2)


# Tool dispatch table
TOOL_HANDLERS = {
    "context_check": do_context_check,
    "context_top_sources": do_context_top_sources,
    "context_suggest": do_context_suggest,
    "context_history": do_context_history,
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="context_check",
            description="Context health check: cumulative session cost + estimated current window usage. Returns token counts, usage%, health level (green/yellow/red/critical), top consumers, and optimization suggestions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="context_top_sources",
            description="Ranked list of top token consumers in the current context window. Use to drill down into what's eating the context budget.",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Number of top sources to return (default 15)", "default": 15},
                    "category": {"type": "string", "description": "Optional filter: rules, skills, agent_output, tool_results, chat, system", "default": ""},
                },
                "required": [],
            },
        ),
        Tool(
            name="context_suggest",
            description="Analyze the current context window and suggest what to unload or compress to free tokens. Returns ranked suggestions with estimated token savings.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="context_history",
            description="Session token usage trend — cumulative cost growth over the session timeline with snapshots at intervals.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    if name == "context_top_sources":
        top_n = arguments.get("top_n", 15)
        category = arguments.get("category", "")
        result = await handler(top_n, category)
    else:
        result = await handler()

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
