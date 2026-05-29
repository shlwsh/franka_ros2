import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from ..auth import get_api_key
from ..config import settings
from ..models.vision import VisionEvaluateResponse
from ..services import paper1_iqa

router = APIRouter(tags=['vision'])

_LOG_DIR = Path(__file__).resolve().parents[3] / 'logs' / 'paper1_iqa'


def _allowed_image_path(path: Path) -> bool:
    paper1 = Path(settings.paper1_root).resolve()
    upload = Path(settings.paper1_upload_dir).resolve()
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resolved.is_file():
        return False
    return str(resolved).startswith(str(paper1)) or str(resolved).startswith(str(upload))


def _maybe_debug_copy(dest: Path, debug: bool) -> None:
    if not debug:
        return
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(dest, _LOG_DIR / dest.name)


@router.post('/vision/evaluate', response_model=VisionEvaluateResponse)
async def evaluate_vision(
    request: Request,
    api_key: str = Depends(get_api_key),
    file: UploadFile | None = File(None),
    debug: bool = Query(False, description='Copy input to logs/paper1_iqa/'),
):
    """Edge-IQA via doctor/paper1 edge_iqa (subprocess by default)."""
    content_type = request.headers.get('content-type', '')

    if file is not None and file.filename:
        upload_dir = Path(settings.paper1_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        dest = upload_dir / f'{uuid.uuid4().hex}_{file.filename or "upload.png"}'
        dest.write_bytes(content)
        _maybe_debug_copy(dest, debug)
        return paper1_iqa.evaluate_image_path(dest)

    if 'application/json' in content_type:
        raw = await request.body()
        if not raw:
            raise HTTPException(status_code=400, detail='empty JSON body')
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail='invalid JSON') from exc
        path_str = payload.get('image_path')
        if not path_str:
            raise HTTPException(
                status_code=400,
                detail='provide multipart file or JSON image_path',
            )
        image_path = Path(path_str)
        if not _allowed_image_path(image_path):
            raise HTTPException(
                status_code=403,
                detail='image_path must be under PAPER1_ROOT or upload cache',
            )
        return paper1_iqa.evaluate_image_path(image_path)

    raise HTTPException(
        status_code=400,
        detail='provide multipart file or JSON image_path',
    )
