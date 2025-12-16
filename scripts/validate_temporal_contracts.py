#!/usr/bin/env python3
"""Validate Temporal activity contracts against underlying models.

This script checks that Temporal dataclasses have all required fields
to construct the Pydantic models they interact with.
"""

import sys
sys.path.insert(0, '.')

from dataclasses import fields as dataclass_fields
from pydantic import BaseModel
from typing import get_type_hints

def get_model_required_fields(model_class) -> set:
    """Get required field names from a Pydantic model."""
    required = set()
    for name, field_info in model_class.model_fields.items():
        if field_info.is_required():
            required.add(name)
    return required

def get_dataclass_fields(dc_class) -> set:
    """Get field names from a dataclass."""
    return {f.name for f in dataclass_fields(dc_class)}

def validate_contract(source_name, source_class, target_name, target_class, field_mapping=None):
    """Validate that source has all fields needed by target."""
    print(f"\n{'='*60}")
    print(f"Contract: {source_name} -> {target_name}")
    print(f"{'='*60}")

    source_fields = get_dataclass_fields(source_class)
    target_required = get_model_required_fields(target_class)

    print(f"\nSource fields ({len(source_fields)}): {sorted(source_fields)}")
    print(f"\nTarget required ({len(target_required)}): {sorted(target_required)}")

    # Apply field mapping if provided
    mapped_source = set()
    for f in source_fields:
        if field_mapping and f in field_mapping:
            mapped_source.add(field_mapping[f])
        else:
            mapped_source.add(f)

    missing = target_required - mapped_source
    if missing:
        print(f"\n❌ MISSING FIELDS: {sorted(missing)}")
        return False
    else:
        print(f"\n✅ All required fields present")
        return True

def check_attribute_access(model_class, attributes: list[str]):
    """Check if attributes exist on a model."""
    print(f"\n{'='*60}")
    print(f"Checking attributes on {model_class.__name__}")
    print(f"{'='*60}")

    all_attrs = set(model_class.model_fields.keys())
    print(f"Available fields: {sorted(all_attrs)}")

    missing = []
    for attr in attributes:
        if attr not in all_attrs:
            missing.append(attr)
            print(f"  ❌ '{attr}' - NOT FOUND")
        else:
            print(f"  ✅ '{attr}' - OK")

    return len(missing) == 0

def main():
    print("\n" + "="*60)
    print("TEMPORAL ACTIVITY CONTRACT VALIDATION")
    print("="*60)

    all_valid = True

    # 1. Check ImageMatchResult -> ImageMatch contract
    print("\n\n### 1. IMAGE MATCH CONTRACT ###")
    from src.temporal.activities.match import ImageMatchResult
    from src.models.image_match import ImageMatch

    valid = validate_contract(
        "ImageMatchResult (Temporal)", ImageMatchResult,
        "ImageMatch (Pydantic)", ImageMatch
    )
    all_valid = all_valid and valid

    # 2. Check PerformancePrediction attributes used in score.py
    print("\n\n### 2. PERFORMANCE PREDICTION CONTRACT ###")
    from src.analyzers.performance_predictor import PerformancePrediction

    # These are the attributes accessed in score.py
    attrs_used = ['overall_score', 'confidence', 'component_scores', 'improvements']
    valid = check_attribute_access(PerformancePrediction, attrs_used)
    all_valid = all_valid and valid

    # Check ComponentScore has 'score', 'strengths', 'weaknesses'
    from src.analyzers.performance_predictor import ComponentScore
    print(f"\nChecking ComponentScore fields:")
    attrs_used = ['score', 'strengths', 'weaknesses']
    valid = check_attribute_access(ComponentScore, attrs_used)
    all_valid = all_valid and valid

    # Check Improvement has 'suggestion'
    from src.analyzers.performance_predictor import Improvement
    print(f"\nChecking Improvement fields:")
    attrs_used = ['suggestion']
    valid = check_attribute_access(Improvement, attrs_used)
    all_valid = all_valid and valid

    # 3. Check CopyVariantResult -> CopyVariant
    print("\n\n### 3. COPY VARIANT CONTRACT ###")
    from src.temporal.activities.generate import CopyVariantResult
    from src.models.copy_variant import CopyVariant

    valid = validate_contract(
        "CopyVariantResult (Temporal)", CopyVariantResult,
        "CopyVariant (Pydantic)", CopyVariant
    )
    all_valid = all_valid and valid

    # 4. Check BrandProfileResult
    print("\n\n### 4. BRAND PROFILE CONTRACT ###")
    from src.temporal.activities.extract import BrandProfileResult
    from src.models.brand_profile import BrandProfile

    valid = validate_contract(
        "BrandProfileResult (Temporal)", BrandProfileResult,
        "BrandProfile (Pydantic)", BrandProfile
    )
    all_valid = all_valid and valid

    # Summary
    print("\n\n" + "="*60)
    if all_valid:
        print("✅ ALL CONTRACTS VALID")
    else:
        print("❌ SOME CONTRACTS FAILED - FIX REQUIRED")
    print("="*60)

    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
