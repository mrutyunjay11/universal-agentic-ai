from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import ProjectInfo, IndexStatus, generate_project_id
from app.services.indexing_service import indexing_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    root_path: str
    language: Optional[str] = None


class ProjectRegistry:
    def __init__(self):
        self._projects: dict[str, ProjectInfo] = {}
        self._db_path: str = os.path.join(os.path.dirname(settings.sqlite_path), "projects.json")

    def load(self):
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        info = ProjectInfo(**item)
                        self._projects[info.project_id] = info
            except Exception as e:
                logger.warning("Failed to load projects: %s", e)

    def save(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with open(self._db_path, "w") as f:
            json.dump(
                [p.model_dump() for p in self._projects.values()],
                f,
                default=str,
            )

    def create(self, name: str, root_path: str, language: Optional[str] = None) -> ProjectInfo:
        project_id = generate_project_id()
        abs_path = os.path.abspath(os.path.expanduser(root_path))
        if not os.path.isdir(abs_path):
            raise HTTPException(status_code=400, detail=f"Directory not found: {root_path}")

        file_count = 0
        for root, dirs, files in os.walk(abs_path):
            file_count += len(files)

        info = ProjectInfo(
            project_id=project_id,
            name=name,
            root_path=abs_path,
            language=language,
            file_count=file_count,
        )
        self._projects[project_id] = info
        self.save()
        return info

    def get(self, project_id: str) -> Optional[ProjectInfo]:
        return self._projects.get(project_id)

    def list_all(self) -> list[ProjectInfo]:
        return list(self._projects.values())

    def delete(self, project_id: str):
        self._projects.pop(project_id, None)
        self.save()


project_registry = ProjectRegistry()
project_registry.load()


@router.post("/projects", response_model=ProjectInfo)
async def create_project(request: CreateProjectRequest):
    project = project_registry.create(
        name=request.name,
        root_path=request.root_path,
        language=request.language,
    )
    return project


@router.get("/projects", response_model=list[ProjectInfo])
async def list_projects():
    return project_registry.list_all()


@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    project = project_registry.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    project_registry.delete(project_id)
    return {"status": "deleted"}


@router.post("/projects/{project_id}/index", response_model=IndexStatus)
async def index_project(project_id: str):
    project = project_registry.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await indexing_service.queue_index(
        project_id=project_id,
        project_root=project.root_path,
    )

    return IndexStatus(
        project_id=project_id,
        status="queued",
        files_indexed=0,
        chunks_indexed=0,
        in_progress=True,
    )


@router.get("/projects/{project_id}/index/status", response_model=IndexStatus)
async def get_index_status(project_id: str):
    project = project_registry.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return IndexStatus(
        project_id=project_id,
        status="unknown",
        files_indexed=project.file_count,
        chunks_indexed=0,
        in_progress=False,
    )
