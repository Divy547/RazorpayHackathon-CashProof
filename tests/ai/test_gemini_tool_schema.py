"""Tests that the Gemini tool declarations stay in lockstep with TOOL_SCHEMAS.

Guards against silent drift between the Anthropic-facing TOOL_SCHEMAS
(tools.py) and the Gemini-facing FunctionDeclaration objects built once at
import time in gemini_investigator.py: the two provider adapters must expose
the exact same 8 tools (6 bounded read tools + submit_proposal + abstain),
with the same names and the same JSON-schema parameters, since neither
adapter is allowed to give a model access to anything the other doesn't.
"""

from __future__ import annotations

from cashproof.ai.gemini_investigator import _GEMINI_FUNCTION_DECLARATIONS, _GEMINI_TOOLS
from cashproof.ai.tools import TERMINAL_TOOL_NAMES, TOOL_SCHEMAS


def test_gemini_declares_exactly_the_same_tool_names_as_anthropic() -> None:
    anthropic_names = {schema["name"] for schema in TOOL_SCHEMAS}
    gemini_names = {decl.name for decl in _GEMINI_FUNCTION_DECLARATIONS}

    assert gemini_names == anthropic_names
    assert gemini_names == {
        "get_case_context",
        "get_bridge_breakdown",
        "get_candidates",
        "get_ledger_entry",
        "get_evidence",
        "get_gate_result",
        "submit_proposal",
        "abstain",
    }
    assert TERMINAL_TOOL_NAMES <= gemini_names


def test_gemini_function_declarations_reuse_the_same_json_schema_verbatim() -> None:
    schemas_by_name = {schema["name"]: schema for schema in TOOL_SCHEMAS}

    for decl in _GEMINI_FUNCTION_DECLARATIONS:
        expected = schemas_by_name[decl.name]
        assert decl.description == expected["description"]
        assert decl.parameters_json_schema == expected["input_schema"]


def test_gemini_tools_tuple_wraps_all_declarations_in_a_single_tool() -> None:
    assert len(_GEMINI_TOOLS) == 1
    assert list(_GEMINI_TOOLS[0].function_declarations or []) == list(_GEMINI_FUNCTION_DECLARATIONS)
