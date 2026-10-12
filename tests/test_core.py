"""
Ashiee Core Verification Tests
Validates file operations, tool registry, progressive skills, transcript logs, and agent loop.
"""

import asyncio
from pathlib import Path
from ashiee.config import AshieeConfig, ModelProvider
from ashiee.core.agent import AshieeAgent
from ashiee.tools.file_ops import ViewFileTool, WriteToFileTool, ReplaceFileContentTool
from ashiee.tools.search import FindFilesTool, SearchCodeTool
from ashiee.skills.manager import SkillManager


def test_file_tools(tmp_path):
    async def _test():
        cfg = AshieeConfig(workspace_root=tmp_path)

        # 1. Write file
        writer = WriteToFileTool(cfg)
        res_write = await writer.execute(path="hello.txt", content="Line 1: Hello\nLine 2: World\nLine 3: Ashiee")
        assert res_write.success is True

        # 2. View file
        viewer = ViewFileTool(cfg)
        res_view = await viewer.execute(path="hello.txt", start_line=1, end_line=2)
        assert res_view.success is True
        assert "Line 1: Hello" in res_view.output
        assert "Line 3: Ashiee" not in res_view.output

        # 3. Replace content
        replacer = ReplaceFileContentTool(cfg)
        res_replace = await replacer.execute(
            path="hello.txt",
            target_content="Line 2: World",
            replacement_content="Line 2: Beautiful World"
        )
        assert res_replace.success is True

        # Check updated content
        updated_view = await viewer.execute(path="hello.txt")
        assert "Line 2: Beautiful World" in updated_view.output

    asyncio.run(_test())


def test_search_and_find(tmp_path):
    async def _test():
        cfg = AshieeConfig(workspace_root=tmp_path)
        writer = WriteToFileTool(cfg)
        await writer.execute(path="src/main.py", content="def ashiee_fn():\n    return 42\n")

        finder = FindFilesTool(cfg)
        res_find = await finder.execute(glob_pattern="**/*.py")
        assert res_find.success is True
        assert "main.py" in res_find.output

        searcher = SearchCodeTool(cfg)
        res_search = await searcher.execute(query="ashiee_fn")
        assert res_search.success is True
        assert "ashiee_fn" in res_search.output

    asyncio.run(_test())


def test_skills_discovery():
    cfg = AshieeConfig()
    manager = SkillManager(cfg)
    skills = manager.discover_all()
    assert "code-reviewer" in skills
    assert "test-generator" in skills

    content = manager.load_skill_content("code-reviewer")
    assert content is not None
    assert "Architectural Integrity" in content


def test_agent_execution_loop(tmp_path):
    async def _test():
        cfg = AshieeConfig(workspace_root=tmp_path)
        cfg.llm.provider = ModelProvider.MOCK

        agent = AshieeAgent(cfg)
        response = await agent.execute_turn("Please inspect the repository")

        assert response != ""
        assert (agent.session_dir / "transcript.jsonl").exists()
        assert (agent.session_dir / "transcript_full.jsonl").exists()

    asyncio.run(_test())
