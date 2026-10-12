# Ashiee Autonomous Pair Programmer

Ashiee is an AI-first development system and runtime inspired by Google Antigravity.

## Architectural Principles
1. **ReAct Reasoning Loop**: Multi-turn planning, action execution, and reactive wakeup.
2. **Deterministic File Operations**: Exact matching, contextual line ranges, and safe replacements.
3. **Progressive Disclosure Skills**: Keeps context tokens low by indexing skills as lightweight headers, loading full runbooks only when invoked.
4. **Sandboxed Terminal Execution**: Output size limits, timeouts, and command filtering.
5. **Multi-Agent Orchestrator**: Subagents can be dispatched for dedicated tasks.
6. **Dual-Mode Transcript Logger**: Compact and full JSONL logs.
