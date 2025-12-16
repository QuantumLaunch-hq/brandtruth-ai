# tests/integration/test_database.py
"""Integration tests for database client."""

import os
import pytest

from src.db import Database, CampaignCreate, CampaignStatus, VariantCreate, VariantStatus


# Skip if no database URL
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set"
)


@pytest.fixture
async def db():
    """Create database connection for tests."""
    database = Database()
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture
async def test_user_id(db):
    """Get or create a test user ID."""
    # Check if test user exists
    user = await db.get_user_by_email("test@brandtruth.ai")
    if user:
        return user["id"]

    # Create test user via raw SQL (users managed by NextAuth normally)
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            '''
            INSERT INTO "User" (id, email, name, "createdAt", "updatedAt")
            VALUES (gen_random_uuid()::text, $1, $2, NOW(), NOW())
            ON CONFLICT (email) DO UPDATE SET name = $2
            RETURNING id
            ''',
            "test@brandtruth.ai",
            "Test User"
        )
        return row["id"]


class TestCampaignOperations:
    """Tests for campaign CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_campaign(self, db, test_user_id):
        """Test creating a new campaign."""
        campaign = await db.create_campaign(
            CampaignCreate(
                name="Test Campaign",
                url="https://example.com",
                user_id=test_user_id,
            )
        )

        assert campaign.id is not None
        assert campaign.name == "Test Campaign"
        assert campaign.url == "https://example.com"
        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.user_id == test_user_id

        # Cleanup
        await db.delete_campaign(campaign.id)

    @pytest.mark.asyncio
    async def test_get_campaign(self, db, test_user_id):
        """Test getting a campaign by ID."""
        # Create
        created = await db.create_campaign(
            CampaignCreate(
                name="Get Test",
                url="https://example.com",
                user_id=test_user_id,
            )
        )

        # Get
        campaign = await db.get_campaign(created.id)
        assert campaign is not None
        assert campaign.id == created.id
        assert campaign.name == "Get Test"

        # Cleanup
        await db.delete_campaign(created.id)

    @pytest.mark.asyncio
    async def test_update_campaign_status(self, db, test_user_id):
        """Test updating campaign status."""
        # Create
        campaign = await db.create_campaign(
            CampaignCreate(
                name="Status Test",
                url="https://example.com",
                user_id=test_user_id,
            )
        )

        # Update status
        updated = await db.update_campaign_status(
            campaign.id, CampaignStatus.PROCESSING
        )
        assert updated is not None
        assert updated.status == CampaignStatus.PROCESSING

        # Cleanup
        await db.delete_campaign(campaign.id)

    @pytest.mark.asyncio
    async def test_get_user_campaigns(self, db, test_user_id):
        """Test getting all campaigns for a user."""
        # Create two campaigns
        c1 = await db.create_campaign(
            CampaignCreate(
                name="User Campaign 1",
                url="https://example1.com",
                user_id=test_user_id,
            )
        )
        c2 = await db.create_campaign(
            CampaignCreate(
                name="User Campaign 2",
                url="https://example2.com",
                user_id=test_user_id,
            )
        )

        # Get all
        campaigns = await db.get_user_campaigns(test_user_id)
        campaign_ids = [c.id for c in campaigns]

        assert c1.id in campaign_ids
        assert c2.id in campaign_ids

        # Cleanup
        await db.delete_campaign(c1.id)
        await db.delete_campaign(c2.id)


class TestVariantOperations:
    """Tests for variant CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_variant(self, db, test_user_id):
        """Test creating a new variant."""
        # Create campaign first
        campaign = await db.create_campaign(
            CampaignCreate(
                name="Variant Test Campaign",
                url="https://example.com",
                user_id=test_user_id,
            )
        )

        # Create variant
        variant = await db.create_variant(
            VariantCreate(
                campaign_id=campaign.id,
                headline="Test Headline",
                primary_text="This is the primary text for testing.",
                cta="Learn More",
                angle="benefit",
                emotion="confidence",
            )
        )

        assert variant.id is not None
        assert variant.headline == "Test Headline"
        assert variant.cta == "Learn More"
        assert variant.status == VariantStatus.PENDING

        # Cleanup
        await db.delete_campaign(campaign.id)

    @pytest.mark.asyncio
    async def test_create_variants_batch(self, db, test_user_id):
        """Test creating multiple variants in batch."""
        # Create campaign
        campaign = await db.create_campaign(
            CampaignCreate(
                name="Batch Variant Test",
                url="https://example.com",
                user_id=test_user_id,
            )
        )

        # Create batch of variants
        variants_data = [
            VariantCreate(
                campaign_id=campaign.id,
                headline=f"Headline {i}",
                primary_text=f"Primary text {i}",
                cta="Shop Now",
            )
            for i in range(5)
        ]

        variants = await db.create_variants_batch(variants_data)
        assert len(variants) == 5
        assert all(v.campaign_id == campaign.id for v in variants)

        # Cleanup
        await db.delete_campaign(campaign.id)

    @pytest.mark.asyncio
    async def test_approve_reject_variant(self, db, test_user_id):
        """Test approving and rejecting variants."""
        # Create campaign and variant
        campaign = await db.create_campaign(
            CampaignCreate(
                name="Approval Test",
                url="https://example.com",
                user_id=test_user_id,
            )
        )
        variant = await db.create_variant(
            VariantCreate(
                campaign_id=campaign.id,
                headline="Approval Test",
                primary_text="Testing approval flow",
                cta="Buy Now",
            )
        )

        # Approve
        approved = await db.approve_variant(variant.id)
        assert approved.status == VariantStatus.APPROVED

        # Create another and reject
        variant2 = await db.create_variant(
            VariantCreate(
                campaign_id=campaign.id,
                headline="Reject Test",
                primary_text="Testing rejection flow",
                cta="Buy Now",
            )
        )
        rejected = await db.reject_variant(variant2.id)
        assert rejected.status == VariantStatus.REJECTED

        # Cleanup
        await db.delete_campaign(campaign.id)

    @pytest.mark.asyncio
    async def test_get_campaign_with_variants(self, db, test_user_id):
        """Test getting campaign includes variants."""
        # Create campaign with variants
        campaign = await db.create_campaign(
            CampaignCreate(
                name="With Variants Test",
                url="https://example.com",
                user_id=test_user_id,
            )
        )
        await db.create_variants_batch([
            VariantCreate(
                campaign_id=campaign.id,
                headline=f"Headline {i}",
                primary_text=f"Text {i}",
                cta="CTA",
            )
            for i in range(3)
        ])

        # Get campaign with variants
        fetched = await db.get_campaign(campaign.id)
        assert fetched is not None
        assert len(fetched.variants) == 3

        # Cleanup
        await db.delete_campaign(campaign.id)
