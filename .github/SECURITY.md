# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅        |

Only the latest released version receives security fixes. Please update to the latest version before reporting a vulnerability.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report vulnerabilities by email to: **8935378+gabrielsoltz@users.noreply.github.com**

Include as much of the following as possible:

- Type of vulnerability (e.g. command injection, path traversal, incorrect check logic)
- The affected component (`clauditor/checkers/`, `clauditor/providers/`, a specific check YAML, etc.)
- Steps to reproduce
- Potential impact
- Suggested fix if you have one

You will receive an acknowledgement within 48 hours and a status update within 7 days.

## Scope

In scope:
- Incorrect or bypassable security check logic in `clauditor/checkers/`
- Path traversal or command injection in provider/scanner code
- Privilege escalation when scanning a malicious repository
- False negatives in built-in checks that leave users believing they are secure when they are not

Out of scope:
- Findings about Claude Code itself (report those to Anthropic)
- Issues in third-party dependencies (report to the respective project)
- Social engineering

## Disclosure Policy

We follow coordinated disclosure. Once a fix is ready and released, we will publish a security advisory on GitHub.
