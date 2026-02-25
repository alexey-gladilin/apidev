---
name: security
description: Perform security review of implemented changes with risk classification and actionable findings before final QA approval. Use proactively after tester verification and before QA gate, especially when handling input parsing, auth, secrets, dependencies, or trust boundaries.
---

# Security

Run a focused security review of changed code and return a strict PASS/REJECT decision.
Do not rewrite feature logic in this skill; report vulnerabilities and remediations.

## Pre-Check

If no tester verification evidence is available, stop and output:
`Awaiting Tester verification. Cannot perform security review.`

## Security Context Discovery

Identify security requirements from:
1. `AGENTS.md` and `openspec/AGENTS.md`.
2. `README.md` and security-related docs.
3. Dependency and CI config (`pyproject.toml`, `package.json`, lockfiles, workflow files).

If conventions are unclear, reject with:
`Project security requirements are not documented. Add security conventions and threat assumptions.`

## Security Checklist

### Input and Data Validation
- Validate and sanitize untrusted input.
- Ensure safe parsing and serialization paths.
- Verify output escaping where relevant.

### AuthN/AuthZ and Access Control
- Ensure auth flows are not weakened.
- Enforce authorization at trust boundaries.
- Check for privilege escalation vectors.

### Secrets and Sensitive Data
- Detect hardcoded credentials, keys, tokens.
- Ensure sensitive values are not logged in plaintext.
- Verify secure config/env handling.

### Dependency and Supply Chain Risk
- Review newly introduced dependencies.
- Flag critical/high risk vulnerable packages.
- Confirm lock/version policy compliance.

### Security Design Integrity
- Respect security boundaries in architecture.
- Avoid insecure defaults.
- Avoid error leakage of sensitive internals.

## Analysis Report (Mandatory)

```markdown
## SECURITY ANALYSIS REPORT
- Task ID: #<number>
- Reviewer: Security
- Scope Reviewed: <files/modules>
- Security Requirements Source: <paths>

### Input & Data Validation
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### AuthN/AuthZ & Access Control
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Secrets & Sensitive Data
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Dependency & Supply Chain Risk
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Security Design Integrity
- Status: PASS/FAIL
- Findings:
  1. [File:Line] <finding or "None">

### Summary
- Critical Issues: <count>
- Major Issues: <count>
- Minor Issues: <count>
- Final Recommendation: APPROVE/REJECT
```

## Final Decision

If any check fails:

```markdown
## REJECTION (Security)
- Task ID: #<number>
- Rejection Count: <N+1>
- Severity: CRITICAL / MAJOR / MINOR
- Issues:
  1. [File:Line] <description>
- Required Action: <specific fix instruction>
```

If all checks pass:

```markdown
## SECURITY VERIFIED
- Task ID: #<number>
- Security Review: ✅
- Critical Vulnerabilities: 0
- Major Vulnerabilities: 0
- Tester Infrastructure Evidence: <command/status from tester>
```

Update rejection count in `tasks.md` when rejecting.
