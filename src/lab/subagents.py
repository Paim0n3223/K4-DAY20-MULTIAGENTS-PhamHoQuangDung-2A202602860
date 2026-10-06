"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Delegate here before making changes when you need to inspect task files, "
                "README documents, docstrings, data samples, or logs and identify requirements "
                "and likely root causes."
            ),
            "system_prompt": (
                "You inspect the files specified in the delegation and report evidence. "
                "Read the task requirements and relevant documentation before drawing conclusions. "
                "Do not modify files. Distinguish observed facts from hypotheses, cite file paths, "
                "and report ambiguities, edge cases, and suggested next steps. "
                "Use only information available in the delegated task and its files."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Delegate here when task requirements are known and you need to fix code, "
                "clean data, or produce the requested output files and verify them."
            ),
            "system_prompt": (
                "Implement the delegated task using its requirements and relevant file documentation. "
                "Fix shared root causes rather than individual symptoms. Preserve required output "
                "formats and handle relevant edge cases. Never modify skills or weaken tests. "
                "Run appropriate tests or validation scripts. Report files actually changed, "
                "validation results, and remaining issues; do not claim unverified success."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Delegate here after implementation when you need an independent check of outputs, "
                "task compliance, test results, and edge cases before declaring completion."
            ),
            "system_prompt": (
                "Independently verify the delegated outputs against task requirements, README "
                "documents, and docstrings. Read the actual files and run relevant checks without "
                "modifying files. Check output schemas, edge cases, and claims of completion. "
                "Report concrete findings with file paths and validation evidence, distinguishing "
                "confirmed failures from concerns and checks you could not perform."
            ),
        },
    ]
