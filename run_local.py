#!/usr/bin/env python3
"""Local runner for BrandTruth AI - Brand Extractor (Slice 1).

Usage:
    python run_local.py https://careerfied.ai
    python run_local.py https://example.com --output brand_profile.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.brand_extractor import extract_brand
from src.models.brand_profile import ClaimRiskLevel


console = Console()


def print_brand_profile(profile):
    """Pretty print a brand profile."""
    
    # Header
    console.print(Panel(
        f"[bold blue]{profile.brand_name}[/bold blue]\n"
        f"[dim]{profile.website_url}[/dim]\n"
        f"[italic]{profile.tagline or 'No tagline'}[/italic]",
        title="Brand Profile",
        subtitle=f"Confidence: {profile.confidence_score:.0%}"
    ))
    
    # Value Propositions
    if profile.value_propositions:
        console.print("\n[bold]Value Propositions:[/bold]")
        for vp in profile.value_propositions:
            console.print(f"  • {vp}")
    
    # Target Audience
    if profile.target_audience:
        console.print(f"\n[bold]Target Audience:[/bold] {profile.target_audience}")
    
    # Claims Table
    if profile.claims:
        console.print("\n")
        table = Table(title="Brand Claims", show_header=True)
        table.add_column("Claim", style="cyan", max_width=50)
        table.add_column("Type", style="magenta")
        table.add_column("Risk", style="yellow")
        
        risk_colors = {
            ClaimRiskLevel.LOW: "[green]LOW[/green]",
            ClaimRiskLevel.MEDIUM: "[yellow]MEDIUM[/yellow]",
            ClaimRiskLevel.HIGH: "[red]HIGH[/red]",
            ClaimRiskLevel.BLOCKED: "[red bold]BLOCKED[/red bold]",
        }
        
        for claim in profile.claims[:10]:  # Limit display
            table.add_row(
                claim.claim[:50] + "..." if len(claim.claim) > 50 else claim.claim,
                claim.claim_type,
                risk_colors.get(claim.risk_level, str(claim.risk_level))
            )
        
        console.print(table)
    
    # Social Proof
    if profile.social_proof:
        console.print("\n[bold]Social Proof:[/bold]")
        for sp in profile.social_proof[:5]:
            console.print(f"  [{sp.proof_type}] {sp.content[:80]}...")
            if sp.attribution:
                console.print(f"    — {sp.attribution}")
    
    # Tone
    if profile.tone_markers:
        tones = [f"{t.category.value} ({t.confidence:.0%})" for t in profile.tone_markers]
        console.print(f"\n[bold]Brand Tone:[/bold] {', '.join(tones)}")
    
    if profile.tone_summary:
        console.print(f"[dim]{profile.tone_summary}[/dim]")
    
    # Key Terms
    if profile.key_terms:
        console.print(f"\n[bold]Key Terms:[/bold] {', '.join(profile.key_terms[:10])}")
    
    # Warnings
    if profile.extraction_warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in profile.extraction_warnings:
            console.print(f"  ⚠️  {warning}")
    
    # Pages analyzed
    console.print(f"\n[dim]Analyzed {len(profile.pages_analyzed)} pages[/dim]")


async def main():
    parser = argparse.ArgumentParser(
        description="Extract brand profile from a website"
    )
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path",
        default=None
    )
    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=5,
        help="Maximum pages to scrape (default: 5)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON only"
    )
    
    args = parser.parse_args()
    
    try:
        if not args.json:
            console.print(f"\n[bold]BrandTruth AI - Brand Extractor[/bold]")
            console.print(f"Analyzing: {args.url}\n")
        
        # Extract brand profile
        profile = await extract_brand(args.url)
        
        # Output
        if args.json:
            print(profile.model_dump_json(indent=2))
        else:
            print_brand_profile(profile)
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(profile.model_dump_json(indent=2))
            console.print(f"\n[green]Saved to {output_path}[/green]")
        
        # Also show prompt context
        if not args.json:
            console.print("\n")
            console.print(Panel(
                profile.to_prompt_context(),
                title="Prompt Context (for Copy Generation)",
                subtitle="Use this to constrain ad copy generation"
            ))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
