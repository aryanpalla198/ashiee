"""
Task Management REST Backend
"""
from typing import List, Optional
from pydantic import BaseModel

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

TASKS_STORE: List[Task] = [
    Task(id=1, title="Initialize workspace runtime", completed=True),
    Task(id=2, title="Collaborate with Antigravity engine", completed=True)
]

def list_tasks() -> List[Task]:
    return TASKS_STORE

def add_task(title: str) -> Task:
    t = Task(id=len(TASKS_STORE) + 1, title=title, completed=False)
    TASKS_STORE.append(t)
    return t
