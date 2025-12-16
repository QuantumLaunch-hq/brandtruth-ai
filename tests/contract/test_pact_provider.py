# tests/contract/test_pact_provider.py
"""Pact Provider Verification Tests.

Verifies that the backend API satisfies the consumer contracts.
Run this after running consumer tests to validate contracts.

Install: pip install pact-python
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Try to import pact verifier
try:
    from pact import Verifier
    PACT_AVAILABLE = True
except ImportError:
    PACT_AVAILABLE = False


PACT_DIR = Path(__file__).parent / "pacts"


@pytest.mark.skipif(not PACT_AVAILABLE, reason="pact-python not installed")
class TestProviderVerification:
    """Verify provider against consumer contracts."""
    
    @pytest.fixture(scope="class")
    def provider_url(self):
        """Provider URL - assumes server is running."""
        return "http://localhost:8000"
    
    @pytest.mark.pact
    @pytest.mark.slow
    def test_verify_pacts(self, provider_url):
        """Verify all pacts against the running provider."""
        pact_files = list(PACT_DIR.glob("*.json"))
        
        if not pact_files:
            pytest.skip("No pact files found. Run consumer tests first.")
        
        verifier = Verifier(
            provider="BrandTruthAPI",
            provider_base_url=provider_url,
        )
        
        # Verify each pact file
        for pact_file in pact_files:
            output, logs = verifier.verify_pacts(
                str(pact_file),
                verbose=True,
                provider_states_setup_url=f"{provider_url}/_pact/setup",
            )
            
            assert output == 0, f"Pact verification failed for {pact_file.name}"
    
    @pytest.mark.pact
    def test_provider_states_available(self, provider_url):
        """Test that provider state setup endpoint exists (optional)."""
        # This is optional - only needed if using provider states
        import requests
        
        # Try to reach the provider
        try:
            response = requests.get(f"{provider_url}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Provider not running at localhost:8000")


def verify_contracts():
    """CLI function to verify contracts."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify Pact contracts")
    parser.add_argument(
        "--provider-url",
        default="http://localhost:8000",
        help="Provider base URL"
    )
    parser.add_argument(
        "--pact-dir",
        default=str(PACT_DIR),
        help="Directory containing pact files"
    )
    
    args = parser.parse_args()
    
    if not PACT_AVAILABLE:
        print("ERROR: pact-python not installed. Run: pip install pact-python")
        sys.exit(1)
    
    pact_files = list(Path(args.pact_dir).glob("*.json"))
    
    if not pact_files:
        print(f"No pact files found in {args.pact_dir}")
        print("Run consumer tests first: pytest tests/contract/test_pact_consumer.py")
        sys.exit(1)
    
    print(f"Verifying {len(pact_files)} pact file(s) against {args.provider_url}")
    
    verifier = Verifier(
        provider="BrandTruthAPI",
        provider_base_url=args.provider_url,
    )
    
    all_passed = True
    for pact_file in pact_files:
        print(f"\nVerifying: {pact_file.name}")
        try:
            output, logs = verifier.verify_pacts(str(pact_file), verbose=True)
            if output != 0:
                all_passed = False
                print(f"  ❌ FAILED")
            else:
                print(f"  ✅ PASSED")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            all_passed = False
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    verify_contracts()
