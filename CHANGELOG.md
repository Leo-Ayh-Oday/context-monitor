# Changelog

All notable changes to Context Monitor are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-05

### Added
- Initial release
- `context_check` — health check with usage%, health level, top 3 consumers
- `context_top_sources` — ranked token consumers with category filter
- `context_suggest` — optimization suggestions with token savings estimates
- `context_history` — session timeline with cumulative token growth snapshots
- Dual reporting: cumulative session cost + estimated current context window
- Token counting via tiktoken `o200k_base` with `cl100k_base` fallback
- 7-category classification: rules, skills, agent_output, tool_results, chat, system, claude_md
- MCP stdio transport via `mcp` SDK v1+

[0.1.0]: https://github.com/Leo-Ayh-Oday/context-monitor/releases/tag/v0.1.0
