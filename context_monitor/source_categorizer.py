"""Classify message content by source category for token attribution."""

import re


class SourceCategorizer:
    # Detection patterns for each category
    PATTERNS = {
        "rules": [
            r"rules?[/\\](ecc|zh|common|web|typescript|python|golang|swift|php)",
            r"\.claude[/\\]rules[/\\]",
            r"CLAUDE\.md",
        ],
        "skills": [
            r"skills?[/\\][\w-]+[/\\]SKILL\.md",
            r"skills?[/\\]",
            r"<skill",
            r"skill.*SKILL\.md",
        ],
        "agent_output": [
            r'"type":\s*"user".*"tool_result"',
            r"subagent|agent.*result|agent.*output",
            r"\[Agent:",
        ],
        "claude_md": [
            r"CLAUDE\.md",
        ],
        "system": [
            r'"type":\s*"system"',
            r"system-reminder",
        ],
    }

    def classify(self, message: dict, text: str) -> str:
        """Classify a message into a source category."""
        msg_type = message.get("type", "")

        # System messages
        if msg_type == "system":
            return "system"

        # Check message content for known patterns
        text_lower = text.lower()

        # Rules detection — highest priority since rules files are large
        if self._matches_any(text, self.PATTERNS["rules"]):
            return "rules"

        # Skills detection
        if self._matches_any(text, self.PATTERNS["skills"]):
            return "skills"

        # Agent output detection
        if msg_type == "user":
            content = message.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        # Check if tool_result is from an Agent call
                        tool_use_id = block.get("tool_use_id", "")
                        if "agent" in tool_use_id.lower() or "agent" in str(block).lower()[:200]:
                            return "agent_output"
                        return "tool_results"

        # CLAUDE.md
        if self._matches_any(text, self.PATTERNS["claude_md"]):
            return "claude_md"

        # Chat messages
        if msg_type in ("user", "assistant"):
            return "chat"

        return "other"

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False
