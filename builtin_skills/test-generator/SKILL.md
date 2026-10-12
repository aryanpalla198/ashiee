---
name: test-generator
description: Generates exhaustive, production-grade test suites including boundary tests, error path coverage, and integration tests using pytest or standard runners.
---

# Ashiee Test Generator Skill

When generating tests, adhere to these guidelines:

## 1. Test Suite Standards
- Use idiomatic test frameworks (`pytest` for Python, `vitest`/`jest` for TypeScript).
- Name test functions clearly describing intent: `test_<function>_<scenario>_<expected_result>()`.
- Keep tests isolated; do not share mutable state across tests.

## 2. Test Coverage Matrix
Ensure each generated suite includes:
1. **Happy Path**: Expected valid inputs and typical scenarios.
2. **Boundary Conditions**: Empty inputs, zeros, maximum integers, extreme bounds.
3. **Failure Paths**: Missing files, timeout errors, invalid argument types, expected exceptions.

## 3. Automation
After generating test files, proactively run the test suite using `run_command` (e.g., `pytest tests/`) to guarantee all tests pass green before reporting back.
