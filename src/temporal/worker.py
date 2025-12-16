# src/temporal/worker.py
"""Temporal Worker for BrandTruth AI.

This worker process connects to Temporal and executes workflow activities.
Run this alongside the API server to enable durable workflow execution.

Usage:
    # Start Temporal first
    docker-compose -f docker-compose.temporal.yml up -d

    # Then start the worker
    python -m src.temporal.worker

    # Or with custom settings
    TEMPORAL_HOST=localhost:7234 python -m src.temporal.worker

Environment Variables:
    TEMPORAL_HOST: Temporal server address (default: localhost:7234)
    TEMPORAL_NAMESPACE: Namespace to use (default: default)
    TEMPORAL_TASK_QUEUE: Task queue name (default: brandtruth-pipeline)
"""

import asyncio
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.temporal.workflows.ad_pipeline import AdPipelineWorkflow
from src.temporal.activities.extract import extract_brand_activity
from src.temporal.activities.generate import generate_copy_activity
from src.temporal.activities.match import match_images_activity
from src.temporal.activities.compose import compose_ads_activity
from src.temporal.activities.score import predict_performance_activity
from src.temporal.activities.persist import (
    create_campaign_activity,
    update_campaign_status_activity,
    save_brand_profile_activity,
    save_variants_activity,
    complete_campaign_activity,
    fail_campaign_activity,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "brandtruth-pipeline")


async def run_worker():
    """Start the Temporal worker."""
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")

    # Connect to Temporal
    client = await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )

    logger.info(f"Connected to Temporal namespace: {TEMPORAL_NAMESPACE}")

    # Create worker with all activities
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AdPipelineWorkflow],
        activities=[
            # Pipeline activities
            extract_brand_activity,
            generate_copy_activity,
            match_images_activity,
            compose_ads_activity,
            predict_performance_activity,
            # Database persistence activities
            create_campaign_activity,
            update_campaign_status_activity,
            save_brand_profile_activity,
            save_variants_activity,
            complete_campaign_activity,
            fail_campaign_activity,
        ],
        # Use thread pool for blocking activities
        activity_executor=ThreadPoolExecutor(max_workers=10),
    )

    logger.info(f"Starting worker on task queue: {TASK_QUEUE}")
    logger.info("Registered workflows: AdPipelineWorkflow")
    logger.info("Registered activities: extract, generate, match, compose, score, persist")

    # Handle shutdown gracefully
    shutdown_event = asyncio.Event()

    def handle_shutdown(signum, frame):
        logger.info("Shutdown signal received, stopping worker...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Run worker until shutdown
    async with worker:
        logger.info("Worker running. Press Ctrl+C to stop.")
        await shutdown_event.wait()

    logger.info("Worker stopped")


def main():
    """Entry point for the worker."""
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║          BRANDTRUTH AI - TEMPORAL WORKER                      ║
╠═══════════════════════════════════════════════════════════════╣
║  Temporal Host:    {TEMPORAL_HOST:<40} ║
║  Namespace:        {TEMPORAL_NAMESPACE:<40} ║
║  Task Queue:       {TASK_QUEUE:<40} ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
