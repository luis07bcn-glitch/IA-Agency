from typing import Any
from .datetime_tool import get_current_datetime
from .calculator_tool import calculate
from .file_tool import save_to_file, read_from_file

TOOL_SCHEMAS = [
    {
        "name": "get_current_datetime",
        "description": "Returns the current date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "calculate",
        "description": "Safely evaluates a mathematical expression and returns the result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression, e.g. '(10 + 5) * 2'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "save_to_file",
        "description": "Saves text content to a file in the outputs/ directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename, e.g. 'report.md'"},
                "content": {"type": "string", "description": "Text content to write"},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "read_from_file",
        "description": "Reads the content of a file from the outputs/ directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename to read"}
            },
            "required": ["filename"],
        },
    },
]

_REGISTRY = {
    "get_current_datetime": lambda _: get_current_datetime(),
    "calculate": lambda inp: calculate(inp["expression"]),
    "save_to_file": lambda inp: save_to_file(inp["filename"], inp["content"]),
    "read_from_file": lambda inp: read_from_file(inp["filename"]),
}


def execute_tool(name: str, inputs: dict) -> Any:
    if name not in _REGISTRY:
        return {"error": f"Unknown tool: {name}"}
    return _REGISTRY[name](inputs)


__all__ = ["TOOL_SCHEMAS", "execute_tool"]
