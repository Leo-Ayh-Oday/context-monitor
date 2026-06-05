"""Generate context optimization suggestions based on token distribution."""


class SuggestionEngine:
    UNUSED_THRESHOLD = 10  # rounds without reference before suggesting unload

    def generate(self, dist: dict, messages: list[dict]) -> list[dict]:
        """Generate ranked optimization suggestions from current context window dist.

        dist shape (from estimate_current_context):
          {"estimated_tokens": N, "limit": M, "usage_pct": X, "categories": {...}}
        """
        suggestions = []
        categories = dist.get("categories", {})
        total = dist.get("estimated_tokens", 0)
        pct = dist.get("usage_pct", 0)

        # 1. Rules taking too much of the context window
        rules_tokens = categories.get("rules", 0)
        if rules_tokens > 30000:
            suggestions.append({
                "action": "slim_rules",
                "target": "rules/ directories",
                "tokens_freed": int(rules_tokens * 0.5),
                "reason": f"Rules consume {rules_tokens:,} tokens in current window. Consider loading only language-specific rules for the current project, not all languages. Use /context-suggest to see which directories are unused.",
                "confidence": "high",
            })

        # 2. Skills injection overhead
        skills_tokens = categories.get("skills", 0)
        if skills_tokens > 25000:
            suggestions.append({
                "action": "unload_skills",
                "target": "unused skills",
                "tokens_freed": int(skills_tokens * 0.6),
                "reason": f"Skills take {skills_tokens:,} tokens. Unused skills (not referenced in last 10 turns) can be safely unloaded from context.",
                "confidence": "high",
            })

        # 3. Heavy tool results
        tool_tokens = categories.get("tool_results", 0)
        if tool_tokens > 30000:
            suggestions.append({
                "action": "compress_tool_results",
                "target": "tool results",
                "tokens_freed": int(tool_tokens * 0.3),
                "reason": f"Tool results occupy {tool_tokens:,} tokens. Use .wolf/anatomy.md descriptions instead of re-reading files; summarize long agent outputs.",
                "confidence": "medium",
            })

        # 4. Agent output can be summarized
        agent_tokens = categories.get("agent_output", 0)
        if agent_tokens > 15000:
            suggestions.append({
                "action": "summarize_agents",
                "target": "agent outputs",
                "tokens_freed": int(agent_tokens * 0.5),
                "reason": f"Agent outputs take {agent_tokens:,} tokens. Compress to key findings only; store full output in .wolf/memory.md.",
                "confidence": "medium",
            })

        # 5. Overall usage health
        if pct > 70:
            suggestions.append({
                "action": "session_cleanup",
                "target": "context window",
                "tokens_freed": int(total * 0.3),
                "reason": f"Context window at {pct}%. Consider /clear or session compaction to free space for the next task.",
                "confidence": "high",
            })

        # Sort by tokens_freed desc
        suggestions.sort(key=lambda x: x["tokens_freed"], reverse=True)
        return suggestions
