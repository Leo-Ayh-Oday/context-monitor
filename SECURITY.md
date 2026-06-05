# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Do not open a public issue.** Instead, email [2115464137@qq.com](mailto:2115464137@qq.com) with:

- A clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential impact

You will receive a response within **48 hours**. After the vulnerability is confirmed and patched, we will publish a security advisory and credit you (unless you prefer to remain anonymous).

## Scope

The following are in scope:

- MCP protocol vulnerabilities (injection via tool arguments)
- Session file path traversal
- Token counting denial of service
- Information disclosure via tool outputs

## Best Practices

1. **Keep dependencies updated** — run `pip list --outdated` monthly
2. **Use HTTPS** — MCP runs locally over stdio, no network exposure by default
