---
name: security-audit
description: Comprehensive security audit skill for Claude Code. Use when the user wants to audit code for vulnerabilities, security flaws, or weaknesses. Covers OWASP Top 10, injection attacks, authentication flaws, cryptographic issues, secrets exposure, dependency vulnerabilities, and more. Triggers on: "audit my code", "find security issues", "check for vulnerabilities", "security review", "pentest", "find flaws".
version: 1.0.0
---

# Security Audit Skill

This skill guides a **thorough, systematic security audit** of any codebase or file. The goal is to identify all potential vulnerabilities, from critical exploits to low-severity misconfigurations, and provide actionable remediation guidance.

The user provides code, a file, a repository path, or a description of their stack. Audit everything available.

---

## Phase 0 — Reconnaissance

Before auditing, gather context:
- **Language & framework**: Python/Django, JS/Express, Java/Spring, PHP/Laravel, Go, Rust, etc.
- **Entry points**: HTTP routes, CLI args, file uploads, WebSockets, message queues, cron jobs
- **Trust boundaries**: What data comes from users? From third parties? From the database?
- **Auth model**: Session, JWT, OAuth2, API keys, mTLS?
- **Infrastructure hints**: Cloud provider, containerized, serverless, microservices?

Use this context to **prioritize** which vulnerability classes are most relevant.

---

## Phase 1 — OWASP Top 10 (2021)

Check each category systematically:

### A01 — Broken Access Control
- [ ] Missing authorization checks on routes/endpoints
- [ ] Insecure Direct Object References (IDOR): `GET /users/{id}` without ownership check
- [ ] Privilege escalation paths (user → admin)
- [ ] CORS misconfiguration (`Access-Control-Allow-Origin: *` on sensitive APIs)
- [ ] JWT: missing `aud`/`iss` validation, algorithm confusion (`alg: none`)
- [ ] Forced browsing to unprotected admin paths (`/admin`, `/_debug`, `/.env`)
- [ ] Missing function-level access control (frontend hides button, backend doesn't check)

### A02 — Cryptographic Failures
- [ ] Sensitive data transmitted in plain HTTP (no TLS)
- [ ] Weak algorithms: MD5, SHA1, DES, RC4, ECB mode
- [ ] Hardcoded secrets, API keys, passwords in source code
- [ ] Secrets in environment variables logged or exposed in stack traces
- [ ] Missing `Secure`, `HttpOnly`, `SameSite` flags on cookies
- [ ] Insufficient key length (RSA < 2048, AES < 128)
- [ ] Predictable random values for tokens/nonces (use `secrets` module, not `random`)
- [ ] PII stored unencrypted at rest in DB or logs

### A03 — Injection
- [ ] **SQL Injection**: string concatenation in queries, no parameterized statements
- [ ] **NoSQL Injection**: unsanitized MongoDB/Redis operators (`$where`, `$gt`)
- [ ] **Command Injection**: `subprocess.call(user_input)`, `exec()`, `system()`
- [ ] **LDAP Injection**: unsanitized LDAP filter construction
- [ ] **XPath Injection**: XML query built from user input
- [ ] **Template Injection (SSTI)**: Jinja2/Twig/Pebble with unescaped user input
- [ ] **Log Injection**: newlines in user input written to logs
- [ ] **HTML Injection / XSS**: unescaped output in HTML context (see A03/A07)

### A04 — Insecure Design
- [ ] No rate limiting on login, password reset, OTP endpoints
- [ ] Enumerable usernames/emails via timing attacks or distinct error messages
- [ ] Password reset tokens: short-lived? single-use? cryptographically random?
- [ ] Missing anti-automation (CAPTCHA) on sensitive forms
- [ ] Business logic flaws: negative quantities, price tampering, step skipping
- [ ] Multi-step workflow without server-side state validation

### A05 — Security Misconfiguration
- [ ] Debug mode enabled in production (`DEBUG=True`, stack traces exposed)
- [ ] Default credentials not changed (admin/admin, root/root)
- [ ] Unnecessary HTTP methods enabled (TRACE, PUT on REST APIs)
- [ ] Missing security headers:
  - `Content-Security-Policy`
  - `X-Frame-Options` (Clickjacking)
  - `X-Content-Type-Options: nosniff`
  - `Strict-Transport-Security`
  - `Referrer-Policy`
  - `Permissions-Policy`
- [ ] Directory listing enabled on web server
- [ ] Error messages leak internal paths, versions, stack traces to users
- [ ] Cloud storage buckets public (S3, GCS, Azure Blob)

### A06 — Vulnerable and Outdated Components
- [ ] Dependencies with known CVEs (`npm audit`, `pip-audit`, `trivy`, `snyk`)
- [ ] Pinned versions vs. floating versions (`^1.0.0` can pull breaking/vuln updates)
- [ ] Unmaintained packages (last commit > 2 years, no security patches)
- [ ] Transitive dependencies not reviewed
- [ ] Docker base image out of date (`FROM ubuntu:18.04`)
- [ ] OS-level packages not updated in container

### A07 — Identification and Authentication Failures
- [ ] Weak password policy (no minimum length, no complexity)
- [ ] No account lockout after N failed attempts
- [ ] Sessions not invalidated on logout (server-side session store not cleared)
- [ ] Session fixation: session ID not regenerated after login
- [ ] Long-lived or non-expiring tokens
- [ ] JWT stored in `localStorage` (XSS accessible) instead of `HttpOnly` cookie
- [ ] Missing MFA on admin accounts or sensitive operations
- [ ] "Remember me" tokens stored insecurely or with infinite TTL

### A08 — Software and Data Integrity Failures
- [ ] No integrity check on downloaded artifacts (no checksum/signature verification)
- [ ] CI/CD pipeline injectable (untrusted input in `run:` steps of GitHub Actions)
- [ ] Unsafe deserialization: `pickle.loads()`, Java `ObjectInputStream`, PHP `unserialize()`
- [ ] Auto-update mechanisms without signature verification
- [ ] npm/PyPI packages with typosquatting risk in dependencies

### A09 — Security Logging and Monitoring Failures
- [ ] Authentication events not logged (success, failure, lockout)
- [ ] Sensitive operations not audited (admin actions, data exports, permission changes)
- [ ] Logs contain PII, passwords, tokens, credit card numbers
- [ ] No alerting on suspicious activity (brute force, mass data access)
- [ ] Log files world-readable or stored without integrity protection

### A10 — Server-Side Request Forgery (SSRF)
- [ ] User-controlled URLs fetched server-side without allowlist
- [ ] Missing validation against internal IP ranges (`169.254.x.x`, `10.x.x.x`, `127.x.x.x`)
- [ ] Cloud metadata endpoints accessible (`http://169.254.169.254/`)
- [ ] XML/SVG/PDF parsers that resolve external entities (XXE → SSRF)
- [ ] Webhooks without destination validation

---

## Phase 2 — Language-Specific Checks

### JavaScript / TypeScript / Node.js
- [ ] `eval()`, `Function()`, `setTimeout(string)` with user input
- [ ] Prototype pollution: `obj[key] = value` where key is user-controlled
- [ ] `child_process.exec()` vs `execFile()` (prefer the latter)
- [ ] `req.query` / `req.body` used without validation (use Zod, Joi, Yup)
- [ ] `res.redirect(req.query.url)` — open redirect
- [ ] Regular Expression DoS (ReDoS): catastrophic backtracking patterns
- [ ] `JSON.parse()` without try/catch on untrusted input

### Python
- [ ] `pickle`, `shelve`, `marshal` with untrusted data
- [ ] `subprocess.shell=True` with user input
- [ ] `yaml.load()` instead of `yaml.safe_load()`
- [ ] `__import__()` or `importlib` with user-controlled module names
- [ ] Django: raw SQL via `.raw()` or `.extra()` without parameterization
- [ ] Flask: `render_template_string(user_input)` → SSTI
- [ ] Mass assignment: `Model(**request.data)` without field allowlist

### Java
- [ ] `Runtime.exec()` with user input
- [ ] Java deserialization gadget chains (`ObjectInputStream`)
- [ ] XML parsers without XXE protection (`DocumentBuilderFactory` not hardened)
- [ ] Spring: `@RequestParam` bound directly to sensitive model fields
- [ ] Log4Shell pattern: user input passed to logger without sanitization

### PHP
- [ ] `include`/`require` with user-controlled path (LFI/RFI)
- [ ] `$_GET`/`$_POST` used directly in SQL queries
- [ ] `system()`, `exec()`, `passthru()`, `shell_exec()` with user data
- [ ] `unserialize()` on untrusted data
- [ ] `extract($_REQUEST)` — variable injection
- [ ] Type juggling: `==` vs `===` leading to auth bypass (`"0" == false`)

### Go
- [ ] `os/exec` with user-controlled arguments
- [ ] `text/template` instead of `html/template` for HTML output
- [ ] Integer overflow in arithmetic with user-supplied values
- [ ] `math/rand` instead of `crypto/rand` for security tokens

---

## Phase 3 — Infrastructure & Configuration Audit

### Secrets & Environment
- [ ] `.env` files committed to git (check `.gitignore`)
- [ ] AWS/GCP/Azure credentials in source code
- [ ] SSH private keys, PEM files in repository
- [ ] API keys in frontend JavaScript bundle
- [ ] Secrets in Docker image layers (`docker history`)
- [ ] CI/CD secrets printed in logs (`echo $SECRET`)

### Docker & Containers
- [ ] Running as root inside container (no `USER` directive)
- [ ] `--privileged` flag or excessive capabilities
- [ ] Secrets passed via `ENV` (visible in `docker inspect`)
- [ ] Base image with known CVEs (use `trivy image`)
- [ ] No resource limits (CPU/memory DoS risk)
- [ ] Writable filesystem where read-only would suffice

### Cloud & IaC (Terraform, CloudFormation)
- [ ] S3 bucket `public-read` or `public-read-write` ACL
- [ ] Security group `0.0.0.0/0` on port 22 (SSH), 3389 (RDP), 5432 (Postgres)
- [ ] IAM roles with `*` actions or `*` resources (over-permissive)
- [ ] No encryption at rest for RDS, S3, EBS
- [ ] Logging/CloudTrail disabled
- [ ] MFA not enforced on IAM users

---

## Phase 4 — API Security

- [ ] No authentication on internal/admin endpoints
- [ ] GraphQL: introspection enabled in production, no depth/complexity limiting
- [ ] REST: mass assignment via `PATCH /users/me` accepting `role` field
- [ ] Missing pagination → resource exhaustion / data dump
- [ ] API versioning without deprecation of old insecure versions
- [ ] Verbose error responses exposing internal structure
- [ ] No request size limits (body too large → DoS)
- [ ] HTTP verb tampering (PUT/DELETE not restricted)

---

## Phase 5 — File Handling & Uploads

- [ ] Unrestricted file type upload (no MIME/extension validation)
- [ ] File stored in webroot (directly accessible by URL)
- [ ] Filename not sanitized (path traversal: `../../etc/passwd`)
- [ ] Archives (ZIP/TAR) not extracted safely (zip slip attack)
- [ ] Image processing libraries with known CVEs (ImageMagick, Pillow)
- [ ] SVG uploads (can contain embedded JavaScript)
- [ ] No file size limit (disk exhaustion DoS)

---

## Phase 6 — Dependency & Supply Chain

Run these tools and report findings:

```bash
# JavaScript
npm audit --audit-level=moderate
npx snyk test

# Python
pip-audit
safety check

# Ruby
bundle audit

# Java (Maven)
mvn dependency-check:check

# Docker images
trivy image <image_name>

# General (multi-language)
grype .
```

Flag: HIGH and CRITICAL CVEs, packages with no upstream fix, abandoned packages.

---

## Output Format

Structure findings as follows for each issue found:

```
### [SEVERITY] — Vulnerability Name

**Category**: OWASP A0X / CWE-XXX
**File**: path/to/file.py, line N
**Description**: Clear explanation of what the vulnerability is and why it's dangerous.

**Vulnerable code**:
\`\`\`language
// the problematic snippet
\`\`\`

**Exploit scenario**: Brief description of how an attacker could exploit this.

**Fix**:
\`\`\`language
// the corrected snippet
\`\`\`

**References**: CVE / CWE / OWASP link
```

---

## Severity Classification

| Severity | Definition | Examples |
|----------|-----------|---------|
| 🔴 **CRITICAL** | Direct compromise, data breach, RCE | SQLi, RCE, hardcoded admin creds |
| 🟠 **HIGH** | Significant impact, likely exploitable | Auth bypass, SSRF, IDOR, XXE |
| 🟡 **MEDIUM** | Moderate impact, some conditions needed | CSRF, open redirect, weak crypto |
| 🔵 **LOW** | Minor risk, defense-in-depth | Missing headers, verbose errors |
| ⚪ **INFO** | Best practice improvements | Code quality, logging gaps |

---

## Summary Report Template

After completing all phases, output:

```
## Security Audit Summary

**Audited**: [files / repo / scope]
**Date**: [date]
**Stack**: [language, framework, infra]

### Finding Counts
| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | X |
| 🟠 HIGH     | X |
| 🟡 MEDIUM   | X |
| 🔵 LOW      | X |
| ⚪ INFO     | X |

### Top Priorities (fix these first)
1. [Most critical issue]
2. [Second most critical]
3. [Third most critical]

### Positive Security Controls Observed
- [What's already done well]

### Recommended Next Steps
1. Run dependency scanner in CI/CD (npm audit, pip-audit)
2. Add SAST tool (Semgrep, Bandit, SonarQube)
3. Implement security headers middleware
4. Set up secret scanning (GitGuardian, truffleHog)
5. Schedule quarterly penetration testing
```

---

## Useful References

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [SANS Top 25](https://www.sans.org/top25-software-errors/)
- [Semgrep Rules](https://semgrep.dev/r)
- [NVD CVE Database](https://nvd.nist.gov/)