"""Static relationships derived from Python AST information."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.python_ast import PythonAST


@dataclass(frozen=True)
class PythonSymbol:
    """A top-level Python symbol."""

    name: str
    kind: str
    lineno: int


@dataclass(frozen=True)
class PythonRelationship:
    """A static relationship between Python entities."""

    source: str
    target: str
    kind: str


@dataclass(frozen=True)
class PythonModuleRelationships:
    """Immutable module, symbol, and relationship information."""

    relative_path: Path
    symbols: tuple[PythonSymbol, ...]
    relationships: tuple[PythonRelationship, ...]


class PythonRelationshipAnalyzer:
    """Build static relationships from an existing PythonAST."""

    def analyze(
        self,
        ast_result: PythonAST,
    ) -> PythonModuleRelationships:
        """Return module symbols and their static relationships."""
        symbols: list[PythonSymbol] = []
        relationships: list[PythonRelationship] = []

        module_name = str(ast_result.relative_path)

        for python_class in ast_result.classes:
            symbols.append(
                PythonSymbol(
                    name=python_class.name,
                    kind="class",
                    lineno=python_class.lineno,
                )
            )
            relationships.append(
                PythonRelationship(
                    source=module_name,
                    target=python_class.name,
                    kind="contains",
                )
            )

        for python_function in ast_result.functions:
            symbols.append(
                PythonSymbol(
                    name=python_function.name,
                    kind="function",
                    lineno=python_function.lineno,
                )
            )
            relationships.append(
                PythonRelationship(
                    source=module_name,
                    target=python_function.name,
                    kind="contains",
                )
            )

        for python_import in ast_result.imports:
            relationships.append(
                PythonRelationship(
                    source=module_name,
                    target=python_import.name,
                    kind="imports",
                )
            )

        return PythonModuleRelationships(
            relative_path=ast_result.relative_path,
            symbols=tuple(symbols),
            relationships=tuple(relationships),
        )