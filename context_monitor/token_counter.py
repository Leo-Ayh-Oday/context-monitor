"""Token counting via tiktoken. Uses o200k_base encoding for Claude models."""

import tiktoken


class TokenCounter:
    def __init__(self, model: str = "o200k_base"):
        try:
            self.encoder = tiktoken.get_encoding(model)
        except Exception:
            # Fallback to cl100k_base if o200k_base not available
            self.encoder = tiktoken.get_encoding("cl100k_base")
        self._cache: dict[str, int] = {}

    def count(self, text: str) -> int:
        """Count tokens in text. Caches results for repeated strings."""
        if not text:
            return 0
        key = text[:200]  # approximate cache key
        if key in self._cache:
            return self._cache[key]
        tokens = len(self.encoder.encode(text))
        self._cache[key] = tokens
        return tokens

    def count_batch(self, texts: list[str]) -> list[int]:
        """Count tokens for multiple strings."""
        return [self.count(t) for t in texts]

    def total(self, texts: list[str]) -> int:
        """Sum of token counts for a list of strings."""
        return sum(self.count_batch(texts))
