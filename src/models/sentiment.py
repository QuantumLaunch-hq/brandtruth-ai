# src/models/sentiment.py
"""Sentiment monitoring data models for BrandTruth AI.

These models support Slice 6 - the unique sentiment-aware auto-pause feature
that no competitor has.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SentimentLevel(str, Enum):
    """Sentiment classification levels."""
    VERY_NEGATIVE = "very_negative"  # -1.0 to -0.6
    NEGATIVE = "negative"            # -0.6 to -0.2
    NEUTRAL = "neutral"              # -0.2 to 0.2
    POSITIVE = "positive"            # 0.2 to 0.6
    VERY_POSITIVE = "very_positive"  # 0.6 to 1.0


class MentionSource(str, Enum):
    """Sources for brand mentions."""
    TWITTER = "twitter"
    NEWS = "news"
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    BLOG = "blog"
    FORUM = "forum"
    OTHER = "other"


class AlertSeverity(str, Enum):
    """Severity levels for sentiment alerts."""
    INFO = "info"           # Minor fluctuation, FYI only
    WARNING = "warning"     # Notable change, monitor closely
    CRITICAL = "critical"   # Significant negative spike, consider pausing
    EMERGENCY = "emergency" # Crisis level, auto-pause recommended


class CrisisType(str, Enum):
    """Types of brand crises detected."""
    PRODUCT_ISSUE = "product_issue"
    SERVICE_OUTAGE = "service_outage"
    PR_SCANDAL = "pr_scandal"
    EXECUTIVE_CONTROVERSY = "executive_controversy"
    DATA_BREACH = "data_breach"
    COMPETITOR_ATTACK = "competitor_attack"
    MISINFORMATION = "misinformation"
    INDUSTRY_NEWS = "industry_news"
    GENERAL_NEGATIVE = "general_negative"
    UNKNOWN = "unknown"


class BrandMention(BaseModel):
    """A single brand mention from social/news sources."""
    id: str = Field(description="Unique mention ID")
    brand_name: str
    source: MentionSource
    source_url: Optional[str] = None
    author: Optional[str] = None
    content: str = Field(description="The mention text")
    
    # Sentiment analysis
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Score from -1 (negative) to 1 (positive)")
    sentiment_level: SentimentLevel
    confidence: float = Field(ge=0, le=1, description="Confidence in sentiment classification")
    
    # Metadata
    published_at: datetime
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    reach: Optional[int] = Field(default=None, description="Estimated audience reach")
    engagement: Optional[int] = Field(default=None, description="Likes, shares, comments")
    
    # Analysis
    key_phrases: list[str] = Field(default_factory=list)
    detected_issues: list[str] = Field(default_factory=list)
    
    def is_negative(self) -> bool:
        """Check if mention is negative."""
        return self.sentiment_score < -0.2
    
    def is_critical(self) -> bool:
        """Check if mention is critically negative with high reach."""
        return self.sentiment_score < -0.6 and (self.reach or 0) > 10000


class SentimentSnapshot(BaseModel):
    """Point-in-time sentiment summary for a brand."""
    brand_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Aggregate scores
    overall_score: float = Field(ge=-1.0, le=1.0)
    overall_level: SentimentLevel
    
    # Breakdown by source
    twitter_score: Optional[float] = None
    news_score: Optional[float] = None
    reddit_score: Optional[float] = None
    
    # Volume metrics
    total_mentions: int = 0
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    
    # Trend
    score_change_1h: float = 0.0  # Change in last hour
    score_change_24h: float = 0.0  # Change in last 24 hours
    volume_change_24h: float = 0.0  # Volume change %
    
    # Top concerns
    trending_issues: list[str] = Field(default_factory=list)
    top_negative_phrases: list[str] = Field(default_factory=list)
    
    def is_crisis(self) -> bool:
        """Check if current sentiment indicates a crisis."""
        return (
            self.overall_score < -0.4 or
            self.score_change_1h < -0.3 or
            (self.negative_mentions > self.positive_mentions * 3)
        )
    
    def get_health_status(self) -> str:
        """Get human-readable health status."""
        if self.overall_score >= 0.4:
            return "🟢 Excellent"
        elif self.overall_score >= 0.1:
            return "🟢 Good"
        elif self.overall_score >= -0.1:
            return "🟡 Neutral"
        elif self.overall_score >= -0.4:
            return "🟠 Concerning"
        else:
            return "🔴 Critical"


class SentimentAlert(BaseModel):
    """Alert triggered by sentiment changes."""
    id: str
    brand_name: str
    severity: AlertSeverity
    
    # What triggered it
    trigger_reason: str = Field(description="Human-readable reason for alert")
    crisis_type: CrisisType = CrisisType.UNKNOWN
    
    # Metrics at time of alert
    current_score: float
    previous_score: float
    score_change: float
    negative_spike_percent: float = 0.0
    
    # Evidence
    sample_mentions: list[BrandMention] = Field(default_factory=list, max_length=5)
    trending_keywords: list[str] = Field(default_factory=list)
    
    # Timestamps
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Recommendations
    recommended_action: str = Field(default="Monitor closely")
    affected_ad_themes: list[str] = Field(default_factory=list, description="Ad angles to pause")
    
    def should_auto_pause(self) -> bool:
        """Determine if ads should be auto-paused."""
        return self.severity in (AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY)


class AutoPauseRule(BaseModel):
    """Rule defining when to auto-pause ads."""
    id: str
    brand_name: str
    is_active: bool = True
    
    # Trigger conditions (OR logic)
    min_sentiment_score: Optional[float] = Field(default=-0.5, description="Pause if score drops below this")
    max_negative_percent: Optional[float] = Field(default=60.0, description="Pause if negative % exceeds this")
    score_drop_threshold: Optional[float] = Field(default=-0.3, description="Pause if 1h change exceeds this")
    
    # What to pause
    pause_all_ads: bool = False
    pause_themes: list[str] = Field(default_factory=list, description="Specific themes/angles to pause")
    
    # Exceptions
    exclude_platforms: list[str] = Field(default_factory=list)
    
    # Auto-resume conditions
    auto_resume_score: float = Field(default=0.0, description="Resume when score rises above this")
    auto_resume_delay_hours: int = Field(default=24, description="Min hours before auto-resume")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def evaluate(self, snapshot: SentimentSnapshot) -> bool:
        """Check if this rule should trigger a pause."""
        if not self.is_active:
            return False
        
        triggers = []
        
        if self.min_sentiment_score is not None:
            triggers.append(snapshot.overall_score < self.min_sentiment_score)
        
        if self.max_negative_percent is not None:
            if snapshot.total_mentions > 0:
                neg_percent = (snapshot.negative_mentions / snapshot.total_mentions) * 100
                triggers.append(neg_percent > self.max_negative_percent)
        
        if self.score_drop_threshold is not None:
            triggers.append(snapshot.score_change_1h < self.score_drop_threshold)
        
        return any(triggers)


class SentimentMonitorConfig(BaseModel):
    """Configuration for sentiment monitoring."""
    brand_name: str
    brand_keywords: list[str] = Field(default_factory=list, description="Additional keywords to track")
    competitor_names: list[str] = Field(default_factory=list)
    
    # Monitoring settings
    check_interval_minutes: int = 15
    lookback_hours: int = 24
    
    # Source toggles
    monitor_twitter: bool = True
    monitor_news: bool = True
    monitor_reddit: bool = False
    
    # Alert settings
    alert_on_negative_spike: bool = True
    alert_threshold_score: float = -0.4
    alert_threshold_change: float = -0.2
    
    # Auto-pause rules
    auto_pause_rules: list[AutoPauseRule] = Field(default_factory=list)
    
    # Notification settings
    notify_email: Optional[str] = None
    notify_webhook: Optional[str] = None


class SentimentReport(BaseModel):
    """Comprehensive sentiment report for dashboard display."""
    brand_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_period_hours: int = 24
    
    # Current state
    current_snapshot: SentimentSnapshot
    health_status: str
    
    # Trends
    hourly_scores: list[tuple[datetime, float]] = Field(default_factory=list)
    daily_average: float = 0.0
    weekly_average: float = 0.0
    
    # Alerts
    active_alerts: list[SentimentAlert] = Field(default_factory=list)
    resolved_alerts_24h: int = 0
    
    # Top mentions
    most_positive: list[BrandMention] = Field(default_factory=list, max_length=3)
    most_negative: list[BrandMention] = Field(default_factory=list, max_length=3)
    most_viral: list[BrandMention] = Field(default_factory=list, max_length=3)
    
    # Insights
    key_themes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    
    # Auto-pause status
    ads_paused: bool = False
    pause_reason: Optional[str] = None
    paused_themes: list[str] = Field(default_factory=list)
