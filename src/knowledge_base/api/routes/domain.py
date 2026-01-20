"""
Domain management routes
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from knowledge_base.domain.models import DomainResponse

from ..dependencies import DomainManagerDep

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[DomainResponse])
async def list_domains(domain_manager: DomainManagerDep) -> list[DomainResponse]:
    """List all active domains"""
    try:
        return await domain_manager.list_domains()
    except Exception as e:
        logger.error(f"Failed to list domains: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list domains: {str(e)}")


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str, domain_manager: DomainManagerDep
) -> DomainResponse:
    """Get domain details"""
    try:
        domain = await domain_manager.get_domain(UUID(domain_id))
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    except Exception as e:
        logger.error(f"Failed to get domain: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain: {str(e)}")


@router.get("/{domain_id}/schema")
async def get_domain_schema(
    domain_id: str, domain_manager: DomainManagerDep
) -> dict[str, Any]:
    """Get domain schema (entities and relationships)"""
    try:
        uuid_obj = UUID(domain_id)
        entities = await domain_manager.get_entity_types(uuid_obj)
        relationships = await domain_manager.get_relationship_types(uuid_obj)
        return {"entities": entities, "relationships": relationships}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    except Exception as e:
        logger.error(f"Failed to get domain schema: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get domain schema: {str(e)}"
        )
