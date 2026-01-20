"""
Dependency injection setup for API routes
"""

from typing import Annotated

from fastapi import Depends

from ..community import CommunityDetector
from ..config import get_config
from ..domain import DomainManager
from ..pipeline import KnowledgePipeline
from ..resolver import EntityResolver
from ..summarizer import CommunitySummarizer

config = get_config()

_pipeline: KnowledgePipeline | None = None
_resolver: EntityResolver | None = None
_community_detector: CommunityDetector | None = None
_summarizer: CommunitySummarizer | None = None
_domain_manager: DomainManager | None = None


def get_pipeline() -> KnowledgePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = KnowledgePipeline()
    return _pipeline


def get_domain_manager() -> DomainManager:
    global _domain_manager
    if _domain_manager is None:
        _domain_manager = DomainManager(config.database.connection_string)
    return _domain_manager


def get_resolver() -> EntityResolver:
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver(
            db_conn_str=config.database.connection_string,
            model_name=config.llm.model_name,
        )
    return _resolver


def get_community_detector() -> CommunityDetector:
    global _community_detector
    if _community_detector is None:
        _community_detector = CommunityDetector(
            db_conn_str=config.database.connection_string
        )
    return _community_detector


def get_summarizer() -> CommunitySummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = CommunitySummarizer(
            config.database.connection_string, model_name=config.llm.model_name
        )
    return _summarizer


PipelineDep = Annotated[KnowledgePipeline, Depends(get_pipeline)]
DomainManagerDep = Annotated[DomainManager, Depends(get_domain_manager)]
ResolverDep = Annotated[EntityResolver, Depends(get_resolver)]
CommunityDetectorDep = Annotated[CommunityDetector, Depends(get_community_detector)]
SummarizerDep = Annotated[CommunitySummarizer, Depends(get_summarizer)]
