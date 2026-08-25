from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services.file_service import (
    read_file, write_file, edit_file, list_directory, get_file_hash,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/files/read")
async def api_read_file(
    file_path: str,
    project_root: str = Query(default=settings.project_root),
    line_start: int = Query(default=0),
    line_end: int = Query(default=0),
):
    try:
        content = await read_file(file_path, project_root, line_start, line_end)
        return {"file_path": file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/files/write")
async def api_write_file(
    file_path: str,
    content: str,
    project_root: str = settings.project_root,
    force: bool = False,
):
    try:
        result = await write_file(file_path, content, project_root, force)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/files/edit")
async def api_edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    project_root: str = settings.project_root,
):
    try:
        result = await edit_file(file_path, project_root, old_string, new_string)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/list")
async def api_list_directory(
    dir_path: str,
    project_root: str = Query(default=settings.project_root),
):
    try:
        entries = list_directory(dir_path, project_root)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/hash")
async def api_file_hash(
    file_path: str,
    project_root: str = Query(default=settings.project_root),
):
    hash_val = get_file_hash(file_path, project_root)
    return {"file_path": file_path, "hash": hash_val}
