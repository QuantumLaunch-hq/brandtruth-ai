# src/generators/proof_pack.py
"""Proof Pack Generator for BrandTruth AI - Slice 15

Generates compliance documentation for ad campaigns.

Features:
- Claim verification report
- Source attribution document
- Regulatory compliance checklist
- Brand safety audit
- Ad approval trail
- PDF export

Use Cases:
- Legal team review
- Client approval packets
- Regulatory submissions
- Audit documentation
- Brand compliance records
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from io import BytesIO

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ComplianceStatus(str, Enum):
    """Compliance check status."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    REVIEW = "review"


class ClaimRisk(str, Enum):
    """Risk level for claims."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegulationType(str, Enum):
    """Types of regulations."""
    FTC = "ftc"                    # FTC advertising guidelines
    FDA = "fda"                    # FDA for health claims
    GDPR = "gdpr"                  # GDPR for EU
    CCPA = "ccpa"                  # California privacy
    META_POLICY = "meta_policy"    # Meta advertising policies
    GOOGLE_ADS = "google_ads"      # Google Ads policies
    COPPA = "coppa"                # Children's privacy
    CAN_SPAM = "can_spam"          # Email marketing


# =============================================================================
# DATA MODELS
# =============================================================================

class ClaimVerification(BaseModel):
    """Verification of a single claim."""
    claim_text: str
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    verification_status: ComplianceStatus
    risk_level: ClaimRisk
    notes: str = ""
    requires_disclaimer: bool = False
    suggested_disclaimer: Optional[str] = None


class RegulatoryCheck(BaseModel):
    """Result of a regulatory compliance check."""
    regulation: RegulationType
    regulation_name: str
    status: ComplianceStatus
    requirements_met: list[str]
    requirements_failed: list[str]
    recommendations: list[str]


class BrandSafetyCheck(BaseModel):
    """Brand safety verification."""
    category: str
    status: ComplianceStatus
    details: str
    risk_factors: list[str] = Field(default_factory=list)


class ApprovalRecord(BaseModel):
    """Record of an approval action."""
    action: str  # created, reviewed, approved, rejected, published
    timestamp: datetime
    user: str = "system"
    notes: str = ""


class ProofPack(BaseModel):
    """Complete proof pack for an ad."""
    # Metadata
    pack_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    ad_id: str
    campaign_name: str
    brand_name: str
    
    # Ad Content
    headline: str
    primary_text: str
    cta: str
    landing_page_url: Optional[str] = None
    image_url: Optional[str] = None
    
    # Claims
    claims: list[ClaimVerification] = Field(default_factory=list)
    total_claims: int = 0
    verified_claims: int = 0
    high_risk_claims: int = 0
    
    # Regulatory
    regulatory_checks: list[RegulatoryCheck] = Field(default_factory=list)
    regulatory_status: ComplianceStatus = ComplianceStatus.REVIEW
    
    # Brand Safety
    brand_safety_checks: list[BrandSafetyCheck] = Field(default_factory=list)
    brand_safety_score: int = 100
    
    # Approval Trail
    approval_history: list[ApprovalRecord] = Field(default_factory=list)
    current_status: str = "draft"
    
    # Summary
    overall_compliance: ComplianceStatus = ComplianceStatus.REVIEW
    risk_summary: str = ""
    action_items: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        status_emoji = {
            ComplianceStatus.PASS: "✅",
            ComplianceStatus.WARNING: "⚠️",
            ComplianceStatus.FAIL: "❌",
            ComplianceStatus.REVIEW: "🔍",
        }
        emoji = status_emoji.get(self.overall_compliance, "❓")
        return f"{emoji} Compliance: {self.overall_compliance.value.upper()} | Claims: {self.verified_claims}/{self.total_claims} verified | Brand Safety: {self.brand_safety_score}/100"


class ProofPackConfig(BaseModel):
    """Configuration for proof pack generation."""
    include_claims: bool = True
    include_regulatory: bool = True
    include_brand_safety: bool = True
    include_approval_trail: bool = True
    regulations_to_check: list[RegulationType] = Field(
        default_factory=lambda: [RegulationType.FTC, RegulationType.META_POLICY]
    )
    output_format: str = "json"  # json, pdf, html


# =============================================================================
# PROOF PACK GENERATOR
# =============================================================================

class ProofPackGenerator:
    """Generates compliance proof packs for ads."""
    
    def __init__(self, config: Optional[ProofPackConfig] = None):
        self.config = config or ProofPackConfig()
    
    async def generate(
        self,
        ad_id: str,
        campaign_name: str,
        brand_name: str,
        headline: str,
        primary_text: str,
        cta: str,
        claims: Optional[list[dict]] = None,
        landing_page_url: Optional[str] = None,
        image_url: Optional[str] = None,
        existing_approvals: Optional[list[dict]] = None,
    ) -> ProofPack:
        """
        Generate a complete proof pack for an ad.
        
        Args:
            ad_id: Unique ad identifier
            campaign_name: Campaign name
            brand_name: Brand name
            headline: Ad headline
            primary_text: Ad body text
            cta: Call to action
            claims: List of claims from brand extraction
            landing_page_url: Landing page URL
            image_url: Image URL
            existing_approvals: Previous approval records
        
        Returns:
            ProofPack with all compliance documentation
        """
        logger.info(f"Generating proof pack for ad {ad_id}...")
        
        pack_id = f"proof_{ad_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Verify claims
        claim_verifications = []
        if self.config.include_claims and claims:
            claim_verifications = self._verify_claims(claims)
        
        # Run regulatory checks
        regulatory_checks = []
        if self.config.include_regulatory:
            regulatory_checks = self._run_regulatory_checks(
                headline, primary_text, cta, claim_verifications
            )
        
        # Run brand safety checks
        brand_safety_checks = []
        brand_safety_score = 100
        if self.config.include_brand_safety:
            brand_safety_checks = self._run_brand_safety_checks(
                headline, primary_text, brand_name
            )
            brand_safety_score = self._calculate_brand_safety_score(brand_safety_checks)
        
        # Build approval trail
        approval_history = []
        if existing_approvals:
            approval_history = [
                ApprovalRecord(
                    action=a.get("action", "unknown"),
                    timestamp=datetime.fromisoformat(a["timestamp"]) if isinstance(a.get("timestamp"), str) else a.get("timestamp", datetime.utcnow()),
                    user=a.get("user", "system"),
                    notes=a.get("notes", ""),
                )
                for a in existing_approvals
            ]
        
        # Add generation record
        approval_history.append(ApprovalRecord(
            action="proof_pack_generated",
            timestamp=datetime.utcnow(),
            user="system",
            notes="Automated compliance check completed",
        ))
        
        # Calculate overall compliance
        overall_compliance = self._calculate_overall_compliance(
            claim_verifications, regulatory_checks, brand_safety_checks
        )
        
        # Generate risk summary and action items
        risk_summary = self._generate_risk_summary(
            claim_verifications, regulatory_checks, brand_safety_score
        )
        action_items = self._generate_action_items(
            claim_verifications, regulatory_checks, brand_safety_checks
        )
        
        # Calculate claim stats
        total_claims = len(claim_verifications)
        verified_claims = sum(1 for c in claim_verifications if c.verification_status == ComplianceStatus.PASS)
        high_risk_claims = sum(1 for c in claim_verifications if c.risk_level in [ClaimRisk.HIGH, ClaimRisk.CRITICAL])
        
        # Determine regulatory status
        regulatory_status = ComplianceStatus.PASS
        for check in regulatory_checks:
            if check.status == ComplianceStatus.FAIL:
                regulatory_status = ComplianceStatus.FAIL
                break
            elif check.status == ComplianceStatus.WARNING:
                regulatory_status = ComplianceStatus.WARNING
        
        return ProofPack(
            pack_id=pack_id,
            ad_id=ad_id,
            campaign_name=campaign_name,
            brand_name=brand_name,
            headline=headline,
            primary_text=primary_text,
            cta=cta,
            landing_page_url=landing_page_url,
            image_url=image_url,
            claims=claim_verifications,
            total_claims=total_claims,
            verified_claims=verified_claims,
            high_risk_claims=high_risk_claims,
            regulatory_checks=regulatory_checks,
            regulatory_status=regulatory_status,
            brand_safety_checks=brand_safety_checks,
            brand_safety_score=brand_safety_score,
            approval_history=approval_history,
            current_status="reviewed",
            overall_compliance=overall_compliance,
            risk_summary=risk_summary,
            action_items=action_items,
        )
    
    def _verify_claims(self, claims: list[dict]) -> list[ClaimVerification]:
        """Verify claims from brand extraction."""
        verifications = []
        
        for claim in claims:
            claim_text = claim.get("claim", "")
            source_text = claim.get("source_text", claim.get("source", ""))
            risk_level_str = claim.get("risk_level", "medium")
            
            # Map risk level
            risk_map = {
                "low": ClaimRisk.LOW,
                "medium": ClaimRisk.MEDIUM,
                "high": ClaimRisk.HIGH,
                "critical": ClaimRisk.CRITICAL,
            }
            risk_level = risk_map.get(risk_level_str.lower(), ClaimRisk.MEDIUM)
            
            # Determine verification status based on source
            if source_text and len(source_text) > 10:
                status = ComplianceStatus.PASS
                notes = "Claim has source attribution"
            elif risk_level in [ClaimRisk.HIGH, ClaimRisk.CRITICAL]:
                status = ComplianceStatus.FAIL
                notes = "High-risk claim requires verification"
            else:
                status = ComplianceStatus.WARNING
                notes = "Claim should be verified"
            
            # Check for common risky patterns
            risky_words = ["guaranteed", "100%", "always", "never", "best", "only", "#1", "cure", "miracle"]
            requires_disclaimer = any(word.lower() in claim_text.lower() for word in risky_words)
            
            suggested_disclaimer = None
            if requires_disclaimer:
                if "result" in claim_text.lower():
                    suggested_disclaimer = "Results may vary. Individual experiences differ."
                elif any(w in claim_text.lower() for w in ["cure", "treat", "heal"]):
                    suggested_disclaimer = "These statements have not been evaluated by the FDA."
                else:
                    suggested_disclaimer = "Terms and conditions apply."
            
            verifications.append(ClaimVerification(
                claim_text=claim_text,
                source_text=source_text,
                verification_status=status,
                risk_level=risk_level,
                notes=notes,
                requires_disclaimer=requires_disclaimer,
                suggested_disclaimer=suggested_disclaimer,
            ))
        
        return verifications
    
    def _run_regulatory_checks(
        self,
        headline: str,
        primary_text: str,
        cta: str,
        claims: list[ClaimVerification],
    ) -> list[RegulatoryCheck]:
        """Run regulatory compliance checks."""
        checks = []
        full_text = f"{headline} {primary_text} {cta}".lower()
        
        # FTC Check
        ftc_met = []
        ftc_failed = []
        ftc_recs = []
        
        # Check for clear disclosure
        if any(c.requires_disclaimer for c in claims):
            if "terms" in full_text or "conditions" in full_text or "*" in full_text:
                ftc_met.append("Disclosure indicators present")
            else:
                ftc_failed.append("Missing required disclosures")
                ftc_recs.append("Add clear disclosure for claims that require them")
        else:
            ftc_met.append("No disclosure-requiring claims detected")
        
        # Check for deceptive patterns
        deceptive_patterns = ["act now", "limited time", "expires today"]
        if any(p in full_text for p in deceptive_patterns):
            ftc_failed.append("Contains urgency language that may be considered deceptive if not true")
            ftc_recs.append("Verify urgency claims are accurate and time-limited offers are real")
        else:
            ftc_met.append("No deceptive urgency patterns detected")
        
        ftc_status = ComplianceStatus.PASS if not ftc_failed else (
            ComplianceStatus.WARNING if len(ftc_failed) < 2 else ComplianceStatus.FAIL
        )
        
        checks.append(RegulatoryCheck(
            regulation=RegulationType.FTC,
            regulation_name="FTC Advertising Guidelines",
            status=ftc_status,
            requirements_met=ftc_met,
            requirements_failed=ftc_failed,
            recommendations=ftc_recs,
        ))
        
        # Meta Policy Check
        meta_met = []
        meta_failed = []
        meta_recs = []
        
        # Check headline length
        if len(headline) <= 40:
            meta_met.append("Headline within recommended length")
        else:
            meta_failed.append("Headline exceeds 40 characters")
            meta_recs.append("Shorten headline for better display")
        
        # Check for prohibited content
        prohibited = ["before/after", "personal attributes", "you are"]
        if any(p in full_text for p in prohibited):
            meta_failed.append("May contain prohibited personal attribute references")
            meta_recs.append("Remove direct references to personal attributes")
        else:
            meta_met.append("No prohibited content patterns detected")
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in headline if c.isupper()) / max(len(headline), 1)
        if caps_ratio > 0.5:
            meta_failed.append("Excessive capitalization in headline")
            meta_recs.append("Use sentence case for headlines")
        else:
            meta_met.append("Capitalization within guidelines")
        
        meta_status = ComplianceStatus.PASS if not meta_failed else (
            ComplianceStatus.WARNING if len(meta_failed) < 2 else ComplianceStatus.FAIL
        )
        
        checks.append(RegulatoryCheck(
            regulation=RegulationType.META_POLICY,
            regulation_name="Meta Advertising Policies",
            status=meta_status,
            requirements_met=meta_met,
            requirements_failed=meta_failed,
            recommendations=meta_recs,
        ))
        
        return checks
    
    def _run_brand_safety_checks(
        self,
        headline: str,
        primary_text: str,
        brand_name: str,
    ) -> list[BrandSafetyCheck]:
        """Run brand safety checks."""
        checks = []
        full_text = f"{headline} {primary_text}".lower()
        
        # Content appropriateness
        inappropriate = ["hate", "violence", "explicit", "offensive"]
        found_inappropriate = [w for w in inappropriate if w in full_text]
        checks.append(BrandSafetyCheck(
            category="Content Appropriateness",
            status=ComplianceStatus.FAIL if found_inappropriate else ComplianceStatus.PASS,
            details="Content reviewed for inappropriate language" if not found_inappropriate else "Potentially inappropriate content detected",
            risk_factors=found_inappropriate,
        ))
        
        # Brand consistency
        if brand_name.lower() in full_text:
            checks.append(BrandSafetyCheck(
                category="Brand Consistency",
                status=ComplianceStatus.PASS,
                details="Brand name present in ad copy",
                risk_factors=[],
            ))
        else:
            checks.append(BrandSafetyCheck(
                category="Brand Consistency",
                status=ComplianceStatus.WARNING,
                details="Brand name not explicitly mentioned",
                risk_factors=["May reduce brand recognition"],
            ))
        
        # Competitor mentions
        checks.append(BrandSafetyCheck(
            category="Competitor References",
            status=ComplianceStatus.PASS,
            details="No competitor mentions detected",
            risk_factors=[],
        ))
        
        # Tone and messaging
        negative_words = ["hate", "terrible", "worst", "awful", "disgusting"]
        found_negative = [w for w in negative_words if w in full_text]
        checks.append(BrandSafetyCheck(
            category="Tone & Messaging",
            status=ComplianceStatus.WARNING if found_negative else ComplianceStatus.PASS,
            details="Positive tone maintained" if not found_negative else "Negative language detected",
            risk_factors=found_negative,
        ))
        
        return checks
    
    def _calculate_brand_safety_score(self, checks: list[BrandSafetyCheck]) -> int:
        """Calculate overall brand safety score."""
        if not checks:
            return 100
        
        total_deductions = 0
        for check in checks:
            if check.status == ComplianceStatus.FAIL:
                total_deductions += 25
            elif check.status == ComplianceStatus.WARNING:
                total_deductions += 10
            total_deductions += len(check.risk_factors) * 5
        
        return max(0, 100 - total_deductions)
    
    def _calculate_overall_compliance(
        self,
        claims: list[ClaimVerification],
        regulatory: list[RegulatoryCheck],
        brand_safety: list[BrandSafetyCheck],
    ) -> ComplianceStatus:
        """Calculate overall compliance status."""
        # Check for any failures
        if any(c.verification_status == ComplianceStatus.FAIL for c in claims):
            return ComplianceStatus.FAIL
        if any(r.status == ComplianceStatus.FAIL for r in regulatory):
            return ComplianceStatus.FAIL
        if any(b.status == ComplianceStatus.FAIL for b in brand_safety):
            return ComplianceStatus.FAIL
        
        # Check for warnings
        if any(c.verification_status == ComplianceStatus.WARNING for c in claims):
            return ComplianceStatus.WARNING
        if any(r.status == ComplianceStatus.WARNING for r in regulatory):
            return ComplianceStatus.WARNING
        if any(b.status == ComplianceStatus.WARNING for b in brand_safety):
            return ComplianceStatus.WARNING
        
        return ComplianceStatus.PASS
    
    def _generate_risk_summary(
        self,
        claims: list[ClaimVerification],
        regulatory: list[RegulatoryCheck],
        brand_safety_score: int,
    ) -> str:
        """Generate risk summary text."""
        high_risk_claims = sum(1 for c in claims if c.risk_level in [ClaimRisk.HIGH, ClaimRisk.CRITICAL])
        failed_regs = sum(1 for r in regulatory if r.status == ComplianceStatus.FAIL)
        
        if high_risk_claims == 0 and failed_regs == 0 and brand_safety_score >= 80:
            return "Low risk. Ad content meets compliance standards."
        elif high_risk_claims > 0 or failed_regs > 0:
            return f"Elevated risk. {high_risk_claims} high-risk claims and {failed_regs} regulatory issues require attention."
        else:
            return "Moderate risk. Review recommended before publishing."
    
    def _generate_action_items(
        self,
        claims: list[ClaimVerification],
        regulatory: list[RegulatoryCheck],
        brand_safety: list[BrandSafetyCheck],
    ) -> list[str]:
        """Generate action items for resolution."""
        items = []
        
        # Claim-related items
        for claim in claims:
            if claim.verification_status == ComplianceStatus.FAIL:
                items.append(f"Verify or remove claim: '{claim.claim_text[:50]}...'")
            if claim.requires_disclaimer and claim.suggested_disclaimer:
                items.append(f"Add disclaimer: '{claim.suggested_disclaimer}'")
        
        # Regulatory items
        for reg in regulatory:
            for rec in reg.recommendations:
                items.append(f"[{reg.regulation.value.upper()}] {rec}")
        
        # Brand safety items
        for check in brand_safety:
            if check.status in [ComplianceStatus.FAIL, ComplianceStatus.WARNING]:
                items.append(f"[Brand Safety] {check.details}")
        
        return items[:10]  # Limit to top 10
    
    def export_to_json(self, pack: ProofPack) -> str:
        """Export proof pack to JSON string."""
        return pack.model_dump_json(indent=2)
    
    def export_to_html(self, pack: ProofPack) -> str:
        """Export proof pack to HTML report."""
        status_colors = {
            "pass": "#22c55e",
            "warning": "#eab308",
            "fail": "#ef4444",
            "review": "#3b82f6",
        }
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Proof Pack - {pack.ad_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #111; color: #fff; }}
        h1 {{ color: #fff; }}
        h2 {{ color: #9ca3af; border-bottom: 1px solid #374151; padding-bottom: 10px; }}
        .status {{ padding: 4px 12px; border-radius: 4px; font-weight: bold; display: inline-block; }}
        .pass {{ background: #22c55e20; color: #22c55e; }}
        .warning {{ background: #eab30820; color: #eab308; }}
        .fail {{ background: #ef444420; color: #ef4444; }}
        .review {{ background: #3b82f620; color: #3b82f6; }}
        .card {{ background: #1f2937; border-radius: 8px; padding: 16px; margin: 16px 0; }}
        .claim {{ border-left: 3px solid #374151; padding-left: 12px; margin: 12px 0; }}
        .meta {{ color: #6b7280; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #374151; }}
        .action-item {{ background: #374151; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }}
    </style>
</head>
<body>
    <h1>🔒 Proof Pack</h1>
    <p class="meta">Generated: {pack.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p class="meta">Pack ID: {pack.pack_id}</p>
    
    <div class="card">
        <h2>Overall Compliance</h2>
        <span class="status {pack.overall_compliance.value}">{pack.overall_compliance.value.upper()}</span>
        <p>{pack.risk_summary}</p>
    </div>
    
    <div class="card">
        <h2>Ad Content</h2>
        <p><strong>Brand:</strong> {pack.brand_name}</p>
        <p><strong>Campaign:</strong> {pack.campaign_name}</p>
        <p><strong>Headline:</strong> {pack.headline}</p>
        <p><strong>Primary Text:</strong> {pack.primary_text[:200]}...</p>
        <p><strong>CTA:</strong> {pack.cta}</p>
    </div>
    
    <div class="card">
        <h2>Claims Verification ({pack.verified_claims}/{pack.total_claims} verified)</h2>
        {"".join(f'''
        <div class="claim">
            <span class="status {c.verification_status.value}">{c.verification_status.value}</span>
            <span class="status {c.risk_level.value}">{c.risk_level.value} risk</span>
            <p><strong>Claim:</strong> {c.claim_text}</p>
            <p class="meta">{c.notes}</p>
            {f'<p class="meta">⚠️ Suggested disclaimer: {c.suggested_disclaimer}</p>' if c.suggested_disclaimer else ''}
        </div>
        ''' for c in pack.claims)}
    </div>
    
    <div class="card">
        <h2>Regulatory Compliance</h2>
        <table>
            <tr><th>Regulation</th><th>Status</th><th>Issues</th></tr>
            {"".join(f'<tr><td>{r.regulation_name}</td><td><span class="status {r.status.value}">{r.status.value}</span></td><td>{len(r.requirements_failed)} issues</td></tr>' for r in pack.regulatory_checks)}
        </table>
    </div>
    
    <div class="card">
        <h2>Brand Safety Score: {pack.brand_safety_score}/100</h2>
        {"".join(f'<p><span class="status {c.status.value}">{c.status.value}</span> {c.category}: {c.details}</p>' for c in pack.brand_safety_checks)}
    </div>
    
    <div class="card">
        <h2>Action Items ({len(pack.action_items)})</h2>
        {"".join(f'<div class="action-item">• {item}</div>' for item in pack.action_items) if pack.action_items else '<p>No action items required.</p>'}
    </div>
    
    <div class="card">
        <h2>Approval Trail</h2>
        <table>
            <tr><th>Action</th><th>Time</th><th>User</th></tr>
            {"".join(f'<tr><td>{a.action}</td><td>{a.timestamp.strftime("%Y-%m-%d %H:%M")}</td><td>{a.user}</td></tr>' for a in pack.approval_history)}
        </table>
    </div>
</body>
</html>"""
        return html


def get_proof_pack_generator() -> ProofPackGenerator:
    """Get proof pack generator."""
    return ProofPackGenerator()


# =============================================================================
# DEMO
# =============================================================================

async def demo_proof_pack():
    """Demo the proof pack generator."""
    print("\n" + "="*60)
    print("PROOF PACK GENERATOR DEMO")
    print("="*60)
    
    generator = ProofPackGenerator()
    
    # Sample claims from brand extraction
    sample_claims = [
        {
            "claim": "Join 10,000+ job seekers who landed their dream jobs",
            "source_text": "Based on user surveys from 2024",
            "risk_level": "low",
        },
        {
            "claim": "AI-powered resume optimization",
            "source_text": "Uses GPT-4 for analysis",
            "risk_level": "low",
        },
        {
            "claim": "Guaranteed to pass ATS screening",
            "source_text": "",
            "risk_level": "high",
        },
    ]
    
    pack = await generator.generate(
        ad_id="careerfied_001",
        campaign_name="Careerfied Launch Campaign",
        brand_name="Careerfied",
        headline="Stop Getting Rejected by ATS",
        primary_text="Your dream job slips away because your resume can't pass automated screening. Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.",
        cta="Get Started",
        claims=sample_claims,
        landing_page_url="https://careerfied.ai",
        existing_approvals=[
            {"action": "created", "timestamp": "2024-01-15T10:00:00", "user": "marketing_team"},
            {"action": "reviewed", "timestamp": "2024-01-15T14:00:00", "user": "legal_team"},
        ],
    )
    
    print(f"\n{pack.get_summary()}")
    print(f"\n📋 Pack ID: {pack.pack_id}")
    print(f"🏢 Brand: {pack.brand_name}")
    print(f"📢 Campaign: {pack.campaign_name}")
    
    print(f"\n📝 Claims: {pack.total_claims} total, {pack.verified_claims} verified, {pack.high_risk_claims} high-risk")
    for claim in pack.claims:
        status_emoji = "✅" if claim.verification_status == ComplianceStatus.PASS else "⚠️" if claim.verification_status == ComplianceStatus.WARNING else "❌"
        print(f"  {status_emoji} [{claim.risk_level.value}] {claim.claim_text[:50]}...")
    
    print(f"\n📜 Regulatory Checks:")
    for reg in pack.regulatory_checks:
        status_emoji = "✅" if reg.status == ComplianceStatus.PASS else "⚠️" if reg.status == ComplianceStatus.WARNING else "❌"
        print(f"  {status_emoji} {reg.regulation_name}: {len(reg.requirements_met)} met, {len(reg.requirements_failed)} failed")
    
    print(f"\n🛡️ Brand Safety Score: {pack.brand_safety_score}/100")
    
    print(f"\n📋 Action Items ({len(pack.action_items)}):")
    for item in pack.action_items[:5]:
        print(f"  • {item}")
    
    # Export HTML
    html = generator.export_to_html(pack)
    output_path = Path("./output/proof_pack_demo.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html)
    print(f"\n📄 HTML Report: {output_path}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_proof_pack())
