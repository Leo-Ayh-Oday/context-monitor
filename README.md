# Context Monitor MCP

Your Claude Code session's real-time token dashboard — see exactly what's eating your context window.

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/Leo-Ayh-Oday/context-monitor/releases)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://pypi.org/project/context-monitor-mcp/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

**Topics:** `claude-code` `mcp-server` `token-monitor` `context-window` `developer-tools` `tiktoken` `observability` `ai-tools`

## What It Does

Context Monitor is an MCP server that reads your Claude Code session logs and tells you exactly where your context tokens are going. Think of it like Task Manager for your context window — one command and you see the full picture.

```
Health: 🟢 47.5% | 95,060 / 200,000 tokens
chat    ████████████████████  46.1%
skills  █████████████         30.8%
rules   ██████████            23.1%

Unused skills → unload to save 17.5K tokens
```

## Why

Claude Code sessions slow down when context gets full. But **what** is filling it? Rules? Skills? Agent output? This tool gives you hard numbers instead of guesses.

## Quick Start

```bash
pip install context-monitor-mcp
```

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "context-monitor": {
      "command": "python",
      "args": ["-m", "context_monitor.server"],
      "cwd": "~/.claude/mcp-servers/context-monitor"
    }
  }
}
```

Restart Claude Code. The 4 tools appear automatically.

| Tool | What It Does |
|------|-------------|
| `context_check` | Full health: usage%, health level, top 3 consumers, suggestions |
| `context_top_sources` | Ranked token consumers with previews |
| `context_suggest` | What to unload/compress, ranked by savings |
| `context_history` | Token growth trend over session timeline |

## How It Works

```
Session JSONL → tiktoken (o200k_base) → 7 categories → Report + Suggestions
```

1. Reads the latest session JSONL from `~/.claude/projects/`
2. Extracts text from `message.content[].text` blocks only
3. Counts tokens with tiktoken's `o200k_base` encoder (Claude's native encoding)
4. Categorizes: `rules`, `skills`, `agent_output`, `tool_results`, `chat`, `system`, `claude_md`

## Dual Reporting

| Metric | Meaning |
|--------|---------|
| **Cumulative** | Total tokens across entire session (includes repeated system prompts) |
| **Current Window** | Estimated active context — walks backwards from last message until limit |

Cumulative cost might be 200K but current window could be 40% of that. Both matter.

## Accuracy

- Encoder: `o200k_base` with `cl100k_base` fallback
- ±5% approximate — true context varies by system prompt, caching, etc.
- Caching on repeated identical strings

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)

## License

MIT
