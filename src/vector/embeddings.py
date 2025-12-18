# src/vector/embeddings.py
"""Embedding generation service for vector search.

This module provides:
- Azure OpenAI or OpenAI text-embedding-3-small for semantic embeddings
- Batch embedding generation for efficiency
- Domain-specific embedding strategies for brands and ads

Supports both:
- Azure OpenAI (uses AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)
- OpenAI (uses OPENAI_API_KEY)

Azure is preferred if configured.

Usage:
    service = await get_embedding_service()

    # Embed single text
    vector = await service.embed_text("Your text here")

    # Embed brand profile
    vector = await service.embed_brand_profile(brand_profile)

    # Embed ad copy
    vector = await service.embed_copy_variant(copy_variant)
"""

import os
from typing import Optional, Union

from openai import AsyncOpenAI, AsyncAzureOpenAI

from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Async embedding generation with Azure OpenAI or OpenAI.

    Prefers Azure OpenAI if configured, falls back to OpenAI.
    Uses text-embedding-3-small for cost-effective semantic embeddings.
    """

    _instance: Optional['EmbeddingService'] = None

    # Model names
    OPENAI_MODEL = "text-embedding-3-small"  # 1536 dimensions
    AZURE_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    DIMENSIONS = 1536
    BATCH_SIZE = 100  # OpenAI limit: 2048 per request

    def __init__(self):
        self._client: Optional[Union[AsyncOpenAI, AsyncAzureOpenAI]] = None
        self._model: str = self.OPENAI_MODEL
        self._is_azure: bool = False
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> 'EmbeddingService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """Initialize the OpenAI/Azure OpenAI client."""
        if self._initialized:
            return

        # Try Azure OpenAI first (preferred)
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")

        if azure_endpoint and azure_api_key:
            try:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_api_key,
                    api_version="2024-02-01",
                )
                self._model = self.AZURE_DEPLOYMENT
                self._is_azure = True
                logger.info(f"Initialized Azure OpenAI embedding service: {self._model}")
                self._initialized = True
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI: {e}")

        # Fall back to OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                self._client = AsyncOpenAI(api_key=openai_api_key)
                self._model = self.OPENAI_MODEL
                self._is_azure = False
                logger.info(f"Initialized OpenAI embedding service: {self._model}")
                self._initialized = True
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

        logger.warning("No embedding API configured - set AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_API_KEY or OPENAI_API_KEY")

    async def embed_text(self, text: str, dimensions: Optional[int] = None) -> list[float]:
        """Embed a single text string.

        Args:
            text: Text to embed
            dimensions: Optional dimension truncation (512, 768, 1024, 1536)

        Returns:
            Embedding vector (list of floats)
        """
        vectors = await self.embed_batch([text], dimensions)
        return vectors[0] if vectors else [0.0] * self.DIMENSIONS

    async def embed_batch(
        self,
        texts: list[str],
        dimensions: Optional[int] = None,
    ) -> list[list[float]]:
        """Embed multiple texts efficiently.

        Args:
            texts: List of text strings to embed
            dimensions: Optional dimension reduction (512, 768, 1024, 1536)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        if self._client is None:
            logger.warning("Embedding service not available, returning zero vectors")
            dims = dimensions or self.DIMENSIONS
            return [[0.0] * dims for _ in texts]

        dims = dimensions or self.DIMENSIONS

        # Batch the requests
        all_embeddings = []
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]

            try:
                # Azure doesn't support dimensions parameter for all models
                create_params = {
                    "model": self._model,
                    "input": batch,
                }
                # Only add dimensions for OpenAI (not Azure)
                if not self._is_azure:
                    create_params["dimensions"] = dims

                response = await self._client.embeddings.create(**create_params)

                # Extract vectors in order
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

                logger.debug(f"Embedded batch {i // self.BATCH_SIZE + 1} ({len(batch)} texts)")

            except Exception as e:
                logger.error(f"Failed to embed batch: {e}")
                # Return zero vectors on failure
                all_embeddings.extend([[0.0] * dims for _ in batch])

        logger.info(f"Embedded {len(texts)} texts -> {dims}d vectors")
        return all_embeddings

    async def embed_brand_profile(self, brand_profile: dict) -> list[float]:
        """Create semantic embedding for a brand profile.

        Strategy: Combine key brand elements into a rich text representation
        that captures the brand's essence for similarity matching.

        Args:
            brand_profile: BrandProfile dict with brand_name, tagline, etc.

        Returns:
            Embedding vector (1536 dimensions)
        """
        # Construct rich text representation
        text_parts = [
            f"Brand: {brand_profile.get('brand_name', 'Unknown')}",
            f"Industry: {brand_profile.get('industry', 'general')}",
        ]

        if brand_profile.get("tagline"):
            text_parts.append(f"Tagline: {brand_profile['tagline']}")

        if brand_profile.get("value_propositions"):
            vps = "; ".join(brand_profile["value_propositions"][:3])
            text_parts.append(f"Value: {vps}")

        if brand_profile.get("tone_summary"):
            text_parts.append(f"Tone: {brand_profile['tone_summary']}")

        if brand_profile.get("key_terms"):
            terms = ", ".join(brand_profile["key_terms"][:10])
            text_parts.append(f"Keywords: {terms}")

        # Combine into single text
        embedding_text = ". ".join(text_parts)

        # Generate embedding
        vector = await self.embed_text(embedding_text)
        return vector

    async def embed_copy_variant(self, copy_variant: dict) -> list[float]:
        """Create semantic embedding for ad copy.

        Strategy: Combine headline + primary_text + angle/emotion context
        for semantic similarity matching.

        Args:
            copy_variant: CopyVariant dict with headline, primary_text, angle, emotion

        Returns:
            Embedding vector (1536 dimensions)
        """
        # Construct embedding text
        embedding_text = f"{copy_variant.get('headline', '')}. {copy_variant.get('primary_text', '')}"

        # Add context for better semantic understanding
        angle = copy_variant.get("angle", "")
        emotion = copy_variant.get("emotion", "")
        if angle or emotion:
            context = f" [Angle: {angle}, Emotion: {emotion}]"
            embedding_text += context

        # Generate embedding
        vector = await self.embed_text(embedding_text)
        return vector

    async def embed_search_query(self, query: str) -> list[float]:
        """Embed a search query.

        Simple pass-through for now, but could apply query-specific
        transformations in the future.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        return await self.embed_text(query)


# Singleton accessor
async def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance.

    Returns:
        EmbeddingService instance
    """
    return await EmbeddingService.get_instance()
