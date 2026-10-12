---
name: code-reviewer
description: Performs rigorous, professional code reviews evaluating correctness, edge cases, potential memory leaks, security vulnerabilities, and adherence to clean architecture principles.
---

# Ashiee Code Reviewer Skill

When activated, follow these disciplined review phases:

## 1. Architectural Integrity
- Verify that single responsibility principle is maintained.
- Ensure loose coupling and high cohesion across modules.
- Check for dependency inversion: high-level modules should not depend on low-level implementation details.

## 2. Safety & Security
- Inspect for injection vulnerabilities (SQL, Command, XSS).
- Verify input boundary sanitization.
- Check file system path traversal defenses (`Path.resolve()` with workspace root validation).

## 3. Performance & Resource Leaks
- Check open file handles, database connections, and subprocess streams.
- Identify algorithmic bottlenecks: O(N^2) or nested loops where O(N) is feasible.

## 4. Verification Output Format
Structure your review findings as follows:
- **Summary**: Concise high-level evaluation.
- **Critical Issues (Blockers)**: Bugs, memory leaks, security exploits.
- **Improvements (Non-blocking)**: Readability, idiomatic style, micro-optimizations.
- **Proposed Diff**: Provide exact code patches or replacements.
