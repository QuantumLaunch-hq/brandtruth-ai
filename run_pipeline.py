#!/usr/bin/env python3
"""Run full pipeline: Brand Extraction → Copy Generation → Image Matching → Ad Composition.

Usage:
    python run_pipeline.py https://careerfied.ai
    python run_pipeline.py https://example.com --variants 5 --output campaign.json
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

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.brand_extractor import extract_brand
from src.generators.copy_generator import generate_copy
from src.composers.image_matcher import match_images
from src.composers.image_matcher_v2 import match_images_v2
from src.composers.ad_composer import compose_ads
from src.models.copy_variant import Platform
from src.models.composed_ad import AdFormat


console = Console()


def print_copy_variants(result):
    """Pretty print copy generation results."""
    
    console.print(Panel(
        f"[bold green]{result.brand_name}[/bold green] - {result.total_generated} Variants\n"
        f"[dim]Compliant: {result.compliant_count}/{result.total_generated} | "
        f"Time: {result.generation_time_seconds:.1f}s[/dim]",
        title="Copy Generation Complete",
    ))
    
    # Group by angle
    angles = {}
    for variant in result.variants:
        angle = variant.angle.value
        if angle not in angles:
            angles[angle] = []
        angles[angle].append(variant)
    
    # Print each variant (condensed)
    for i, variant in enumerate(result.variants, 1):
        compliance_status = "✅" if (variant.compliance and variant.compliance.overall_compliant) else "⚠️"
        console.print(f"  {i}. [{variant.angle.value}] {compliance_status} {variant.headline}")
    
    # Summary table
    console.print("")
    table = Table(title="Angle Distribution", show_header=True)
    table.add_column("Angle", style="cyan")
    table.add_column("Count", justify="right")
    
    for angle, variants in sorted(angles.items()):
        table.add_row(angle, str(len(variants)))
    
    console.print(table)


def print_image_matches(batch_result):
    """Pretty print image matching results (condensed)."""
    
    console.print(Panel(
        f"[bold green]Images Matched[/bold green]\n"
        f"Variants: {batch_result.total_variants} | "
        f"Total Images: {batch_result.total_matches} | "
        f"Time: {batch_result.total_time_seconds:.1f}s",
        title="Image Matching Complete",
    ))
    
    # Just show count per variant
    for result in batch_result.results:
        best = result.get_best_match()
        if best:
            console.print(f"  • Variant {result.copy_variant_id[-2:]}: {len(result.matches)} images, best score: {best.match_score:.2f}")


def print_composed_ads(batch_result):
    """Pretty print composed ads results."""
    
    console.print(Panel(
        f"[bold green]Ads Composed[/bold green]\n"
        f"Requested: {batch_result.total_requested} | "
        f"Composed: {batch_result.total_composed} | "
        f"Total Assets: {batch_result.total_assets} | "
        f"Time: {batch_result.total_time_seconds:.1f}s",
        title="Ad Composition Complete",
    ))
    
    # List files
    console.print("\n[bold]Generated Files:[/bold]")
    for ad in batch_result.ads:
        console.print(f"\n  [cyan]Ad {ad.id}[/cyan]: {ad.headline[:40]}...")
        for format_key, asset in ad.assets.items():
            size_kb = asset.file_size_bytes / 1024 if asset.file_size_bytes else 0
            console.print(f"    • {format_key}: {asset.file_path} ({size_kb:.0f} KB)")
    
    if batch_result.errors:
        console.print("\n[yellow]Errors:[/yellow]")
        for error in batch_result.errors:
            console.print(f"  ⚠️  {error}")


async def main():
    parser = argparse.ArgumentParser(
        description="Run full ad creation pipeline"
    )
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument(
        "--variants", "-n",
        type=int,
        default=10,
        help="Number of copy variants to generate (default: 10)"
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["meta", "linkedin", "google"],
        default="meta",
        help="Target platform (default: meta)"
    )
    parser.add_argument(
        "--objective", "-o",
        choices=["awareness", "traffic", "conversions"],
        default="conversions",
        help="Campaign objective (default: conversions)"
    )
    parser.add_argument(
        "--offer",
        help="Specific offer to promote",
        default=None
    )
    parser.add_argument(
        "--images", "-i",
        type=int,
        default=3,
        help="Number of images per variant (default: 3)"
    )
    parser.add_argument(
        "--vision",
        action="store_true",
        help="Use vision-enhanced image matching (slower but better quality)"
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image matching step"
    )
    parser.add_argument(
        "--skip-compose",
        action="store_true",
        help="Skip ad composition step"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory to save composed ads"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path",
        default=None
    )
    parser.add_argument(
        "--profile",
        help="Path to cached brand profile JSON",
        default=None
    )
    parser.add_argument(
        "--logo",
        help="Path to logo image file",
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        console.print(Panel(
            "[bold]BrandTruth AI Pipeline[/bold]\n"
            f"URL: {args.url}\n"
            f"Platform: {args.platform.upper()}\n"
            f"Objective: {args.objective}\n"
            f"Variants: {args.variants}\n"
            f"Vision Mode: {'✓ Enabled' if args.vision else 'Off'}\n"
            f"Output: {args.output_dir}",
            title="Configuration"
        ))
        
        # Step 1: Brand Extraction
        if args.profile and Path(args.profile).exists():
            console.print("\n[bold]Step 1: Loading cached brand profile...[/bold]")
            from src.models.brand_profile import BrandProfile
            profile_data = json.loads(Path(args.profile).read_text())
            profile = BrandProfile(**profile_data)
            console.print(f"[green]✓ Loaded profile for {profile.brand_name}[/green]")
        else:
            console.print("\n[bold]Step 1: Extracting brand profile...[/bold]")
            profile = await extract_brand(args.url)
            console.print(f"[green]✓ Extracted profile for {profile.brand_name} (confidence: {profile.confidence_score:.0%})[/green]")
            
            # Save profile for reuse
            profile_path = Path(f"brand_profile_{profile.brand_name.lower().replace(' ', '_')}.json")
            profile_path.write_text(profile.model_dump_json(indent=2))
            console.print(f"[dim]Saved to {profile_path}[/dim]")
        
        # Step 2: Copy Generation
        console.print("\n[bold]Step 2: Generating copy variants...[/bold]")
        
        platform_map = {
            "meta": Platform.META,
            "linkedin": Platform.LINKEDIN,
            "google": Platform.GOOGLE,
        }
        
        copy_result = generate_copy(
            brand_profile=profile,
            objective=args.objective,
            platform=platform_map[args.platform],
            num_variants=args.variants,
            offer=args.offer,
        )
        
        print_copy_variants(copy_result)
        
        # Step 3: Image Matching
        image_result = None
        image_matches = {}
        
        if not args.skip_images:
            import os
            if os.getenv("UNSPLASH_ACCESS_KEY"):
                if args.vision:
                    console.print("\n[bold]Step 3: Matching images (with vision analysis)...[/bold]")
                    image_result = match_images_v2(
                        copy_variants=copy_result.variants,
                        images_per_variant=args.images,
                    )
                else:
                    console.print("\n[bold]Step 3: Matching images...[/bold]")
                    image_result = match_images(
                        copy_variants=copy_result.variants,
                        images_per_variant=args.images,
                    )
                print_image_matches(image_result)
                
                # Build image_matches dict (best image per variant)
                for result in image_result.results:
                    best = result.get_best_match()
                    if best:
                        image_matches[result.copy_variant_id] = best
            else:
                console.print("\n[yellow]Step 3: Skipping image matching (UNSPLASH_ACCESS_KEY not set)[/yellow]")
        
        # Step 4: Ad Composition
        composition_result = None
        
        if not args.skip_compose and image_matches:
            console.print("\n[bold]Step 4: Composing ads...[/bold]")
            
            composition_result = compose_ads(
                copy_variants=copy_result.variants,
                image_matches=image_matches,
                output_dir=args.output_dir,
                formats=[AdFormat.SQUARE, AdFormat.PORTRAIT, AdFormat.STORY],
            )
            
            print_composed_ads(composition_result)
        elif args.skip_compose:
            console.print("\n[yellow]Step 4: Skipping ad composition (--skip-compose)[/yellow]")
        elif not image_matches:
            console.print("\n[yellow]Step 4: Skipping ad composition (no images matched)[/yellow]")
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_data = {
                "brand_profile": json.loads(profile.model_dump_json()),
                "copy_result": json.loads(copy_result.model_dump_json()),
            }
            if image_result:
                output_data["image_result"] = json.loads(image_result.model_dump_json())
            if composition_result:
                output_data["composition_result"] = json.loads(composition_result.model_dump_json())
            
            output_path.write_text(json.dumps(output_data, indent=2, default=str))
            console.print(f"\n[green]✓ Saved results to {output_path}[/green]")
        
        # Final summary
        composed_count = composition_result.total_composed if composition_result else 0
        asset_count = composition_result.total_assets if composition_result else 0
        
        console.print(Panel(
            f"[bold green]Pipeline Complete[/bold green]\n\n"
            f"Brand: {profile.brand_name}\n"
            f"Variants generated: {copy_result.total_generated}\n"
            f"Images matched: {len(image_matches)}\n"
            f"Ads composed: {composed_count}\n"
            f"Total assets: {asset_count}\n\n"
            f"Output directory: {args.output_dir}",
            title="Summary"
        ))
        
        if composition_result and composition_result.ads:
            console.print("\n[bold green]🎉 Your ads are ready![/bold green]")
            console.print(f"[dim]Check the {args.output_dir} folder for your ad images.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
