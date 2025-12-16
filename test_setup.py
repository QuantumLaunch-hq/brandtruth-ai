#!/usr/bin/env python3
"""Quick test to verify installation."""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    
    try:
        from src.models.brand_profile import BrandProfile, BrandClaim, ToneMarker
        print("  ✓ Models import OK")
    except ImportError as e:
        print(f"  ✗ Models import failed: {e}")
        return False
    
    try:
        from src.extractors.scraper import WebScraper, ScrapedPage
        print("  ✓ Scraper import OK")
    except ImportError as e:
        print(f"  ✗ Scraper import failed: {e}")
        return False
    
    try:
        from src.extractors.brand_extractor import BrandExtractor
        print("  ✓ Brand extractor import OK")
    except ImportError as e:
        print(f"  ✗ Brand extractor import failed: {e}")
        return False
    
    return True


def test_models():
    """Test model instantiation."""
    print("\nTesting models...")
    
    from src.models.brand_profile import (
        BrandProfile, BrandAssets, BrandClaim, 
        ClaimRiskLevel, ToneMarker, ToneCategory
    )
    
    # Create a test profile
    profile = BrandProfile(
        brand_name="Test Brand",
        website_url="https://example.com",
        tagline="Test tagline",
        value_propositions=["Value 1", "Value 2"],
        claims=[
            BrandClaim(
                claim="We save you time",
                claim_type="benefit",
                risk_level=ClaimRiskLevel.LOW,
                source_url="https://example.com",
                source_text="Our product saves you time.",
            )
        ],
        tone_markers=[
            ToneMarker(
                category=ToneCategory.PROFESSIONAL,
                confidence=0.9,
                evidence="Formal language throughout",
                source_url="https://example.com",
            )
        ],
    )
    
    print(f"  ✓ Created profile for: {profile.brand_name}")
    print(f"  ✓ Safe claims: {len(profile.get_safe_claims())}")
    print(f"  ✓ Dominant tone: {profile.get_dominant_tone()}")
    
    # Test JSON serialization
    json_str = profile.model_dump_json()
    print(f"  ✓ JSON serialization OK ({len(json_str)} bytes)")
    
    # Test prompt context
    context = profile.to_prompt_context()
    print(f"  ✓ Prompt context generated ({len(context)} chars)")
    
    return True


def test_env():
    """Check environment setup."""
    print("\nChecking environment...")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"  ✓ ANTHROPIC_API_KEY is set ({api_key[:10]}...)")
    else:
        print("  ⚠ ANTHROPIC_API_KEY not set (copy .env.example to .env)")
    
    return True


def main():
    print("=" * 50)
    print("BrandTruth AI - Installation Test")
    print("=" * 50)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_models()
    all_passed &= test_env()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your ANTHROPIC_API_KEY")
        print("  3. Run: playwright install chromium")
        print("  4. Test: python run_local.py https://careerfied.ai")
    else:
        print("✗ Some tests failed. Check errors above.")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
