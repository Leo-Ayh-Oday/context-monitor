"""Quick validation test for context-monitor MCP server."""
import sys, json, asyncio
sys.path.insert(0, '.')

from token_counter import TokenCounter
from source_categorizer import SourceCategorizer
from suggestion_engine import SuggestionEngine
from server import parse_jsonl_session, compute_session_stats, estimate_current_context, health_level
from server import do_context_check, do_context_top_sources, do_context_suggest, do_context_history

async def main():
    print('1. Imports OK')

    path = r'C:\Users\ZhuanZ（无密码）\.claude\projects\C--Users-ZhuanZ-------claude\ad93732f-cab0-4d03-bcf1-1a5dcd0102ae.jsonl'
    msgs = parse_jsonl_session(path)
    print(f'2. Parsed {len(msgs):,} messages from session')

    cum = compute_session_stats(msgs)
    print(f'3. Cumulative session cost: {cum["cumulative_total"]:,} tokens')

    cur = estimate_current_context(msgs)
    print(f'4. Current window: {cur["estimated_tokens"]:,} / {cur["limit"]:,} = {cur["usage_pct"]:.1f}%')
    print(f'   Health: {health_level(cur["usage_pct"])}')
    for cat, n in sorted(cur['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f'     {cat}: {n:,} tokens ({n/max(cur["estimated_tokens"],1)*100:.1f}%)')

    result = json.loads(await do_context_check())
    print(f'5. context_check tool: window {result["current_window"]["usage_pct"]}% health={result["current_window"]["health"]}')

    result2 = json.loads(await do_context_suggest())
    print(f'6. context_suggest: {len(result2["suggestions"])} suggestions, savable={result2["total_savable"]:,}')

    result3 = json.loads(await do_context_history())
    print(f'7. context_history: {len(result3["snapshots"])} snapshots over {result3["total_messages"]:,} messages')

    print('\nALL TESTS PASSED')

asyncio.run(main())
