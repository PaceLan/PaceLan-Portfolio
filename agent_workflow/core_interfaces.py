"""Unified core interfaces for Project, Task, Run, Execution, Result, and Record."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Project:
    """A single independent project."""

    project_id: str


@dataclass(frozen=True)
class Task:
    """A task belonging to a project."""

    task_id: str
    project_id: str


@dataclass(frozen=True)
class Run:
    """One execution run of a task."""

    run_id: str
    task_id: str


@dataclass(frozen=True)
class Execution:
    """Execution state belonging to a run."""

    run_id: str
    status: str


@dataclass(frozen=True)
class Result:
    """Result state belonging to a run."""

    run_id: str
    status: str


@dataclass(frozen=True)
class Record:
    """A persistent historical or snapshot record."""

    record_id: str
    project_id: str
    run_id: str
    data: Any = None