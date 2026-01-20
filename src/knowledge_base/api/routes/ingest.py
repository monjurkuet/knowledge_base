"""
Text and file ingestion routes
"""

import logging
import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..dependencies import PipelineDep

logger = logging.getLogger(__name__)
router = APIRouter()


class IngestTextRequest(BaseModel):
    text: str
    filename: str | None = "uploaded_text.txt"
    channel_id: str | None = None
    domain_id: str | None = None


@router.post("/text")
async def ingest_text(
    request: IngestTextRequest,
    pipeline: PipelineDep = None,
) -> dict[str, str]:
    """Ingest text content directly"""
    try:
        temp_file = f"/tmp/{request.filename}"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(request.text)

        await pipeline.run(
            temp_file, channel_id=request.channel_id, domain_id=request.domain_id
        )

        os.remove(temp_file)

        return {
            "status": "success",
            "message": f"Successfully ingested {len(request.text)} characters",
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/file")
async def ingest_file(
    file: UploadFile = File(...),
    channel_id: str | None = None,
    domain_id: str | None = None,
    pipeline: PipelineDep = None,
) -> dict[str, str]:
    """Upload and ingest a text file"""
    try:
        content = await file.read()
        text = content.decode("utf-8")

        temp_file = f"/tmp/{file.filename}"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(text)

        await pipeline.run(temp_file, channel_id=channel_id, domain_id=domain_id)

        os.remove(temp_file)

        return {
            "status": "success",
            "message": f"Successfully ingested file {file.filename}",
        }

    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")
