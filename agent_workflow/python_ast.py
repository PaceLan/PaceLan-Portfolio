"""Static Python source analysis using the standard-library AST module."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PythonImport:
    """A Python import statement."""

    name: str
    level: int


@dataclass(frozen=True)
class PythonFunction:
    """A top-level Python function."""

    name: str
    lineno: int


@dataclass(frozen=True)
class PythonClass:
    """A top-level Python class."""

    name: str
    lineno: int


@dataclass(frozen=True)
class PythonAST:
    """Immutable structural information extracted from one Python file."""

    relative_path: Path
    imports: tuple[PythonImport, ...]
    classes: tuple[PythonClass, ...]
    functions: tuple[PythonFunction, ...]


class PythonASTAnalyzer:
    """Analyze Python source without executing it."""

    def analyze(
        self,
        path: Path,
        relative_path: Path | None = None,
    ) -> PythonAST:
        source_path = Path(path)

        if not source_path.exists():
            raise FileNotFoundError(
                f"Python source file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise IsADirectoryError(
                f"Python source path is not a file: {source_path}"
            )

        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_path))

        imports: list[PythonImport] = []
        classes: list[PythonClass] = []
        functions: list[PythonFunction] = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        PythonImport(
                            name=alias.name,
                            level=0,
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    PythonImport(
                        name=node.module or "",
                        level=node.level,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                classes.append(
                    PythonClass(
                        name=node.name,
                        lineno=node.lineno,
                    )
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(
                    PythonFunction(
                        name=node.name,
                        lineno=node.lineno,
                    )
                )

        return PythonAST(
            relative_path=(
                Path(relative_path)
                if relative_path is not None
                else source_path
            ),
            imports=tuple(imports),
            classes=tuple(classes),
            functions=tuple(functions),
        )