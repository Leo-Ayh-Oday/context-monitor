# Contributing to Context Monitor

Thanks for contributing. This guide covers dev setup, conventions, and workflow.

## Development Environment

```bash
git clone https://github.com/Leo-Ayh-Oday/context-monitor.git
cd context-monitor
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
```

## Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add category filter to context_top_sources
fix: correct token count for empty content blocks
docs: update MCP config example
test: add integration test for session parsing
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

## Pull Request Workflow

1. **Fork and branch** from `main`
2. **Implement** with tests
3. **Run tests**: `python test_live.py`
4. **Open PR** with description and linked issues

### PR Checklist

- [ ] Tests added for new functionality
- [ ] `python test_live.py` passes
- [ ] No hardcoded secrets
- [ ] Commit messages follow conventional commits format

## Code Style

- Keep functions under 50 lines
- Keep files under 800 lines
- Use type hints on public APIs
- Prefer immutability

## Testing

```bash
python test_live.py
```

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/Leo-Ayh-Oday/context-monitor/discussions)
- **Bugs**: [GitHub Issues](https://github.com/Leo-Ayh-Oday/context-monitor/issues)
- **Security**: see [SECURITY.md](SECURITY.md)
