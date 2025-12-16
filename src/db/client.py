# src/db/client.py
"""Async PostgreSQL database client for BrandTruth AI.

This client connects to the same PostgreSQL database as Prisma,
allowing the Python backend to share data with the Next.js frontend.
"""

import json
import os
from datetime import datetime
from typing import Any
from contextlib import asynccontextmanager

import asyncpg

from src.db.models import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignStatus,
    Variant,
    VariantCreate,
    VariantUpdate,
    VariantStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Singleton instance
_db_instance: "Database | None" = None


def get_database() -> "Database":
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


class Database:
    """Async PostgreSQL database client.

    Matches the Prisma schema used by the Next.js frontend.
    Uses connection pooling for efficient resource usage.
    """

    def __init__(self, dsn: str | None = None):
        """Initialize database client.

        Args:
            dsn: PostgreSQL connection string. Defaults to DATABASE_URL env var.
        """
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URL environment variable not set")

        # Remove Prisma-specific parameters that asyncpg doesn't understand
        # Prisma uses ?schema=public but asyncpg doesn't support this
        if "?" in self.dsn:
            base_url, params = self.dsn.split("?", 1)
            # Filter out schema parameter
            filtered_params = "&".join(
                p for p in params.split("&")
                if not p.startswith("schema=")
            )
            self.dsn = f"{base_url}?{filtered_params}" if filtered_params else base_url

        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Connect to database and create connection pool."""
        if self.pool is not None:
            return

        logger.info("Connecting to database...")
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("Database connection pool created")

    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as conn:
            yield conn

    # =========================================================================
    # Campaign Operations
    # =========================================================================

    async def create_campaign(self, data: CampaignCreate) -> Campaign:
        """Create a new campaign.

        Args:
            data: Campaign creation data

        Returns:
            Created campaign with generated ID
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO "Campaign" (
                    id, name, url, status, "userId", "workflowId", "workflowRunId",
                    "createdAt", "updatedAt"
                )
                VALUES (
                    gen_random_uuid()::text, $1, $2, $3, $4, $5, $6,
                    NOW(), NOW()
                )
                RETURNING *
                ''',
                data.name,
                data.url,
                data.status.value,
                data.user_id,
                data.workflow_id,
                data.workflow_run_id,
            )
            logger.info(f"Created campaign: {row['id']}")
            return Campaign.from_row(dict(row))

    async def get_campaign(self, campaign_id: str) -> Campaign | None:
        """Get a campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign or None if not found
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "Campaign" WHERE id = $1',
                campaign_id,
            )
            if not row:
                return None

            # Also fetch variants
            variants = await self.get_campaign_variants(campaign_id)
            return Campaign.from_row(dict(row), variants)

    async def get_campaign_by_workflow(self, workflow_id: str) -> Campaign | None:
        """Get a campaign by Temporal workflow ID.

        Args:
            workflow_id: Temporal workflow ID

        Returns:
            Campaign or None if not found
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "Campaign" WHERE "workflowId" = $1',
                workflow_id,
            )
            if not row:
                return None
            return Campaign.from_row(dict(row))

    async def get_user_campaigns(self, user_id: str) -> list[Campaign]:
        """Get all campaigns for a user.

        Args:
            user_id: User ID

        Returns:
            List of campaigns ordered by creation date (newest first)
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(
                '''
                SELECT * FROM "Campaign"
                WHERE "userId" = $1
                ORDER BY "createdAt" DESC
                ''',
                user_id,
            )
            campaigns = []
            for row in rows:
                variants = await self.get_campaign_variants(row['id'])
                campaigns.append(Campaign.from_row(dict(row), variants))
            return campaigns

    async def update_campaign(
        self, campaign_id: str, data: CampaignUpdate
    ) -> Campaign | None:
        """Update a campaign.

        Args:
            campaign_id: Campaign ID
            data: Update data (only non-None fields are updated)

        Returns:
            Updated campaign or None if not found
        """
        # Build dynamic update query
        updates = []
        params = []
        param_idx = 1

        if data.name is not None:
            updates.append(f'name = ${param_idx}')
            params.append(data.name)
            param_idx += 1

        if data.status is not None:
            updates.append(f'status = ${param_idx}')
            params.append(data.status.value)
            param_idx += 1

        if data.workflow_id is not None:
            updates.append(f'"workflowId" = ${param_idx}')
            params.append(data.workflow_id)
            param_idx += 1

        if data.workflow_run_id is not None:
            updates.append(f'"workflowRunId" = ${param_idx}')
            params.append(data.workflow_run_id)
            param_idx += 1

        if data.brand_profile is not None:
            updates.append(f'"brandProfile" = ${param_idx}')
            params.append(json.dumps(data.brand_profile))
            param_idx += 1

        if data.budget_result is not None:
            updates.append(f'"budgetResult" = ${param_idx}')
            params.append(json.dumps(data.budget_result))
            param_idx += 1

        if data.audience_result is not None:
            updates.append(f'"audienceResult" = ${param_idx}')
            params.append(json.dumps(data.audience_result))
            param_idx += 1

        if data.completed_at is not None:
            updates.append(f'"completedAt" = ${param_idx}')
            params.append(data.completed_at)
            param_idx += 1

        if not updates:
            return await self.get_campaign(campaign_id)

        # Always update updatedAt
        updates.append('"updatedAt" = NOW()')

        # Add campaign_id as last param
        params.append(campaign_id)

        query = f'''
            UPDATE "Campaign"
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        '''

        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            if not row:
                return None
            return Campaign.from_row(dict(row))

    async def update_campaign_status(
        self, campaign_id: str, status: CampaignStatus
    ) -> Campaign | None:
        """Update campaign status.

        Args:
            campaign_id: Campaign ID
            status: New status

        Returns:
            Updated campaign or None if not found
        """
        return await self.update_campaign(
            campaign_id, CampaignUpdate(status=status)
        )

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and all its variants.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if deleted, False if not found
        """
        async with self.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM "Campaign" WHERE id = $1',
                campaign_id,
            )
            deleted = result == "DELETE 1"
            if deleted:
                logger.info(f"Deleted campaign: {campaign_id}")
            return deleted

    # =========================================================================
    # Variant Operations
    # =========================================================================

    async def create_variant(self, data: VariantCreate) -> Variant:
        """Create a new variant.

        Args:
            data: Variant creation data

        Returns:
            Created variant with generated ID
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO "Variant" (
                    id, "campaignId", headline, "primaryText", cta,
                    angle, emotion, "imageUrl", "composedUrl",
                    score, "scoreDetails", status,
                    "createdAt", "updatedAt"
                )
                VALUES (
                    gen_random_uuid()::text, $1, $2, $3, $4,
                    $5, $6, $7, $8,
                    $9, $10, $11,
                    NOW(), NOW()
                )
                RETURNING *
                ''',
                data.campaign_id,
                data.headline,
                data.primary_text,
                data.cta,
                data.angle,
                data.emotion,
                data.image_url,
                data.composed_url,
                data.score,
                json.dumps(data.score_details) if data.score_details else None,
                data.status.value,
            )
            logger.info(f"Created variant: {row['id']}")
            return Variant.from_row(dict(row))

    async def create_variants_batch(
        self, variants: list[VariantCreate]
    ) -> list[Variant]:
        """Create multiple variants in a single transaction.

        Args:
            variants: List of variant creation data

        Returns:
            List of created variants
        """
        if not variants:
            return []

        async with self.acquire() as conn:
            async with conn.transaction():
                created = []
                for data in variants:
                    row = await conn.fetchrow(
                        '''
                        INSERT INTO "Variant" (
                            id, "campaignId", headline, "primaryText", cta,
                            angle, emotion, "imageUrl", "composedUrl",
                            score, "scoreDetails", status,
                            "createdAt", "updatedAt"
                        )
                        VALUES (
                            gen_random_uuid()::text, $1, $2, $3, $4,
                            $5, $6, $7, $8,
                            $9, $10, $11,
                            NOW(), NOW()
                        )
                        RETURNING *
                        ''',
                        data.campaign_id,
                        data.headline,
                        data.primary_text,
                        data.cta,
                        data.angle,
                        data.emotion,
                        data.image_url,
                        data.composed_url,
                        data.score,
                        json.dumps(data.score_details) if data.score_details else None,
                        data.status.value,
                    )
                    created.append(Variant.from_row(dict(row)))

                logger.info(f"Created {len(created)} variants in batch")
                return created

    async def get_variant(self, variant_id: str) -> Variant | None:
        """Get a variant by ID.

        Args:
            variant_id: Variant ID

        Returns:
            Variant or None if not found
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "Variant" WHERE id = $1',
                variant_id,
            )
            if not row:
                return None
            return Variant.from_row(dict(row))

    async def get_campaign_variants(self, campaign_id: str) -> list[Variant]:
        """Get all variants for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            List of variants
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(
                '''
                SELECT * FROM "Variant"
                WHERE "campaignId" = $1
                ORDER BY "createdAt" ASC
                ''',
                campaign_id,
            )
            return [Variant.from_row(dict(row)) for row in rows]

    async def update_variant(
        self, variant_id: str, data: VariantUpdate
    ) -> Variant | None:
        """Update a variant.

        Args:
            variant_id: Variant ID
            data: Update data (only non-None fields are updated)

        Returns:
            Updated variant or None if not found
        """
        updates = []
        params = []
        param_idx = 1

        if data.headline is not None:
            updates.append(f'headline = ${param_idx}')
            params.append(data.headline)
            param_idx += 1

        if data.primary_text is not None:
            updates.append(f'"primaryText" = ${param_idx}')
            params.append(data.primary_text)
            param_idx += 1

        if data.cta is not None:
            updates.append(f'cta = ${param_idx}')
            params.append(data.cta)
            param_idx += 1

        if data.image_url is not None:
            updates.append(f'"imageUrl" = ${param_idx}')
            params.append(data.image_url)
            param_idx += 1

        if data.composed_url is not None:
            updates.append(f'"composedUrl" = ${param_idx}')
            params.append(data.composed_url)
            param_idx += 1

        if data.score is not None:
            updates.append(f'score = ${param_idx}')
            params.append(data.score)
            param_idx += 1

        if data.score_details is not None:
            updates.append(f'"scoreDetails" = ${param_idx}')
            params.append(json.dumps(data.score_details))
            param_idx += 1

        if data.status is not None:
            updates.append(f'status = ${param_idx}')
            params.append(data.status.value)
            param_idx += 1

        if not updates:
            return await self.get_variant(variant_id)

        updates.append('"updatedAt" = NOW()')
        params.append(variant_id)

        query = f'''
            UPDATE "Variant"
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        '''

        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            if not row:
                return None
            return Variant.from_row(dict(row))

    async def update_variant_status(
        self, variant_id: str, status: VariantStatus
    ) -> Variant | None:
        """Update variant status (approve/reject).

        Args:
            variant_id: Variant ID
            status: New status

        Returns:
            Updated variant or None if not found
        """
        return await self.update_variant(
            variant_id, VariantUpdate(status=status)
        )

    async def approve_variant(self, variant_id: str) -> Variant | None:
        """Approve a variant."""
        return await self.update_variant_status(variant_id, VariantStatus.APPROVED)

    async def reject_variant(self, variant_id: str) -> Variant | None:
        """Reject a variant."""
        return await self.update_variant_status(variant_id, VariantStatus.REJECTED)

    # =========================================================================
    # User Operations (read-only - users managed by NextAuth)
    # =========================================================================

    async def get_user_by_email(self, email: str) -> dict | None:
        """Get a user by email.

        Args:
            email: User email

        Returns:
            User dict or None if not found
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "User" WHERE email = $1',
                email,
            )
            return dict(row) if row else None

    async def get_user(self, user_id: str) -> dict | None:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User dict or None if not found
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "User" WHERE id = $1',
                user_id,
            )
            return dict(row) if row else None
