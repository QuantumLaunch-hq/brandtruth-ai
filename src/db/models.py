# src/db/models.py
"""Database models matching Prisma schema."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CampaignStatus(str, Enum):
    """Campaign status enum matching Prisma schema."""
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    READY = "READY"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VariantStatus(str, Enum):
    """Variant status enum matching Prisma schema."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class CampaignCreate:
    """Data for creating a new campaign."""
    name: str
    url: str
    user_id: str
    status: CampaignStatus = CampaignStatus.DRAFT
    workflow_id: str | None = None
    workflow_run_id: str | None = None


@dataclass
class CampaignUpdate:
    """Data for updating a campaign."""
    name: str | None = None
    status: CampaignStatus | None = None
    workflow_id: str | None = None
    workflow_run_id: str | None = None
    brand_profile: dict | None = None
    budget_result: dict | None = None
    audience_result: dict | None = None
    completed_at: datetime | None = None


@dataclass
class Campaign:
    """Campaign data from database."""
    id: str
    name: str
    url: str
    status: CampaignStatus
    user_id: str
    workflow_id: str | None = None
    workflow_run_id: str | None = None
    brand_profile: dict | None = None
    budget_result: dict | None = None
    audience_result: dict | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    variants: list["Variant"] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict, variants: list["Variant"] | None = None) -> "Campaign":
        """Create Campaign from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            status=CampaignStatus(row["status"]),
            user_id=row["userId"],
            workflow_id=row.get("workflowId"),
            workflow_run_id=row.get("workflowRunId"),
            brand_profile=row.get("brandProfile"),
            budget_result=row.get("budgetResult"),
            audience_result=row.get("audienceResult"),
            created_at=row["createdAt"],
            updated_at=row["updatedAt"],
            completed_at=row.get("completedAt"),
            variants=variants or [],
        )


@dataclass
class VariantCreate:
    """Data for creating a new variant."""
    campaign_id: str
    headline: str
    primary_text: str
    cta: str
    angle: str | None = None
    emotion: str | None = None
    image_url: str | None = None
    composed_url: str | None = None
    score: int | None = None
    score_details: dict | None = None
    status: VariantStatus = VariantStatus.PENDING


@dataclass
class VariantUpdate:
    """Data for updating a variant."""
    headline: str | None = None
    primary_text: str | None = None
    cta: str | None = None
    image_url: str | None = None
    composed_url: str | None = None
    score: int | None = None
    score_details: dict | None = None
    status: VariantStatus | None = None


@dataclass
class Variant:
    """Variant data from database."""
    id: str
    campaign_id: str
    headline: str
    primary_text: str
    cta: str
    angle: str | None = None
    emotion: str | None = None
    image_url: str | None = None
    composed_url: str | None = None
    score: int | None = None
    score_details: dict | None = None
    status: VariantStatus = VariantStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: dict) -> "Variant":
        """Create Variant from database row."""
        return cls(
            id=row["id"],
            campaign_id=row["campaignId"],
            headline=row["headline"],
            primary_text=row["primaryText"],
            cta=row["cta"],
            angle=row.get("angle"),
            emotion=row.get("emotion"),
            image_url=row.get("imageUrl"),
            composed_url=row.get("composedUrl"),
            score=row.get("score"),
            score_details=row.get("scoreDetails"),
            status=VariantStatus(row["status"]),
            created_at=row["createdAt"],
            updated_at=row["updatedAt"],
        )
