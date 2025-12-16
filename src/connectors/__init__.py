# src/connectors/__init__.py
"""Connectors for external platforms."""

from .meta_connector import (
    MetaConnector,
    MockMetaConnector,
    MetaCredentials,
    CampaignConfig,
    AdSetConfig,
    AdCreativeConfig,
    AdConfig,
    TargetingSpec,
    PublishResult,
    CampaignObjective,
    AdSetOptimizationGoal,
    AdStatus,
    get_meta_connector,
)

__all__ = [
    "MetaConnector",
    "MockMetaConnector",
    "MetaCredentials",
    "CampaignConfig",
    "AdSetConfig",
    "AdCreativeConfig",
    "AdConfig",
    "TargetingSpec",
    "PublishResult",
    "CampaignObjective",
    "AdSetOptimizationGoal",
    "AdStatus",
    "get_meta_connector",
]
