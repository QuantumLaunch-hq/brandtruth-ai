# src/extractors/sentiment_monitor.py
"""Sentiment Monitor for BrandTruth AI - Slice 6

This is our UNIQUE differentiator - no competitor has sentiment-aware auto-pause.

Features:
- Monitor news mentions (NewsAPI)
- Monitor social mentions (Twitter/X API)  
- Real-time sentiment scoring using Claude
- Alert system for negative spikes
- Auto-pause rules engine
- Crisis response suggestions
"""

import asyncio
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
import httpx
from anthropic import Anthropic

from src.models.sentiment import (
    BrandMention,
    SentimentSnapshot,
    SentimentAlert,
    SentimentReport,
    SentimentMonitorConfig,
    AutoPauseRule,
    MentionSource,
    SentimentLevel,
    AlertSeverity,
    CrisisType,
)
from src.utils.retry import retry_with_backoff
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SentimentMonitor:
    """Monitor brand sentiment across news and social media."""
    
    def __init__(self, config: SentimentMonitorConfig):
        self.config = config
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Cache for mentions
        self._mentions_cache: list[BrandMention] = []
        self._last_snapshot: Optional[SentimentSnapshot] = None
        
    async def fetch_news_mentions(self, hours_back: int = 24) -> list[BrandMention]:
        """Fetch brand mentions from news sources via NewsAPI."""
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY not set - skipping news monitoring")
            return []
        
        mentions = []
        keywords = [self.config.brand_name] + self.config.brand_keywords
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # NewsAPI limit
        
        from_date = (datetime.utcnow() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%S")
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": self.news_api_key,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
            for article in data.get("articles", []):
                content = f"{article.get('title', '')} {article.get('description', '')}"
                if not content.strip():
                    continue
                    
                mention_id = hashlib.md5(article.get("url", "").encode()).hexdigest()[:12]
                
                mention = BrandMention(
                    id=f"news_{mention_id}",
                    brand_name=self.config.brand_name,
                    source=MentionSource.NEWS,
                    source_url=article.get("url"),
                    author=article.get("author") or article.get("source", {}).get("name"),
                    content=content[:1000],
                    sentiment_score=0.0,  # Will be analyzed
                    sentiment_level=SentimentLevel.NEUTRAL,
                    confidence=0.0,
                    published_at=datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00")),
                    key_phrases=[],
                )
                mentions.append(mention)
                
            logger.info(f"Fetched {len(mentions)} news mentions for {self.config.brand_name}")
            
        except Exception as e:
            logger.error(f"Error fetching news mentions: {e}")
            
        return mentions
    
    async def fetch_twitter_mentions(self, hours_back: int = 24) -> list[BrandMention]:
        """Fetch brand mentions from Twitter/X API."""
        if not self.twitter_bearer:
            logger.warning("TWITTER_BEARER_TOKEN not set - skipping Twitter monitoring")
            return []
        
        mentions = []
        query = f"{self.config.brand_name} -is:retweet lang:en"
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.twitter_bearer}"}
        params = {
            "query": query,
            "max_results": 100,
            "tweet.fields": "created_at,public_metrics,author_id",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                engagement = (
                    metrics.get("like_count", 0) +
                    metrics.get("retweet_count", 0) +
                    metrics.get("reply_count", 0)
                )
                
                mention = BrandMention(
                    id=f"tw_{tweet['id']}",
                    brand_name=self.config.brand_name,
                    source=MentionSource.TWITTER,
                    source_url=f"https://twitter.com/i/status/{tweet['id']}",
                    author=tweet.get("author_id"),
                    content=tweet["text"][:1000],
                    sentiment_score=0.0,
                    sentiment_level=SentimentLevel.NEUTRAL,
                    confidence=0.0,
                    published_at=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
                    engagement=engagement,
                    key_phrases=[],
                )
                mentions.append(mention)
                
            logger.info(f"Fetched {len(mentions)} Twitter mentions for {self.config.brand_name}")
            
        except Exception as e:
            logger.error(f"Error fetching Twitter mentions: {e}")
            
        return mentions
    
    @retry_with_backoff(max_retries=3)
    async def analyze_sentiment_batch(self, mentions: list[BrandMention]) -> list[BrandMention]:
        """Analyze sentiment for a batch of mentions using Claude."""
        if not mentions:
            return []
        
        # Prepare batch for analysis
        mentions_text = "\n\n".join([
            f"[{i}] {m.content[:500]}"
            for i, m in enumerate(mentions[:20])  # Limit batch size
        ])
        
        prompt = f"""Analyze the sentiment of these mentions about "{self.config.brand_name}".

For each mention, provide:
1. sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
2. confidence: float from 0.0 to 1.0
3. key_phrases: list of important phrases (max 3)
4. detected_issues: any problems/complaints mentioned (empty if none)

Return JSON array with objects containing: index, sentiment_score, confidence, key_phrases, detected_issues

Mentions:
{mentions_text}

Return ONLY valid JSON array, no other text."""

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            import json
            text = response.content[0].text.strip()
            # Clean up potential markdown
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            results = json.loads(text)
            
            for result in results:
                idx = result.get("index", 0)
                if idx < len(mentions):
                    mentions[idx].sentiment_score = result.get("sentiment_score", 0.0)
                    mentions[idx].confidence = result.get("confidence", 0.5)
                    mentions[idx].key_phrases = result.get("key_phrases", [])
                    mentions[idx].detected_issues = result.get("detected_issues", [])
                    mentions[idx].sentiment_level = self._score_to_level(mentions[idx].sentiment_score)
                    
        except Exception as e:
            logger.error(f"Error parsing sentiment analysis: {e}")
            # Fallback to neutral
            for m in mentions:
                m.sentiment_level = SentimentLevel.NEUTRAL
                m.confidence = 0.3
        
        return mentions
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """Convert numeric score to sentiment level."""
        if score <= -0.6:
            return SentimentLevel.VERY_NEGATIVE
        elif score <= -0.2:
            return SentimentLevel.NEGATIVE
        elif score <= 0.2:
            return SentimentLevel.NEUTRAL
        elif score <= 0.6:
            return SentimentLevel.POSITIVE
        else:
            return SentimentLevel.VERY_POSITIVE
    
    async def create_snapshot(self, mentions: list[BrandMention]) -> SentimentSnapshot:
        """Create a sentiment snapshot from mentions."""
        if not mentions:
            return SentimentSnapshot(
                brand_name=self.config.brand_name,
                overall_score=0.0,
                overall_level=SentimentLevel.NEUTRAL,
                total_mentions=0,
            )
        
        # Calculate aggregate scores
        total_score = sum(m.sentiment_score * m.confidence for m in mentions)
        total_confidence = sum(m.confidence for m in mentions)
        overall_score = total_score / total_confidence if total_confidence > 0 else 0.0
        
        # Count by sentiment
        positive = sum(1 for m in mentions if m.sentiment_score > 0.2)
        negative = sum(1 for m in mentions if m.sentiment_score < -0.2)
        neutral = len(mentions) - positive - negative
        
        # Score by source
        twitter_mentions = [m for m in mentions if m.source == MentionSource.TWITTER]
        news_mentions = [m for m in mentions if m.source == MentionSource.NEWS]
        
        twitter_score = None
        if twitter_mentions:
            twitter_score = sum(m.sentiment_score for m in twitter_mentions) / len(twitter_mentions)
            
        news_score = None
        if news_mentions:
            news_score = sum(m.sentiment_score for m in news_mentions) / len(news_mentions)
        
        # Collect issues
        all_issues = []
        for m in mentions:
            all_issues.extend(m.detected_issues)
        trending_issues = list(set(all_issues))[:5]
        
        # Calculate change from last snapshot
        score_change_1h = 0.0
        if self._last_snapshot:
            score_change_1h = overall_score - self._last_snapshot.overall_score
        
        snapshot = SentimentSnapshot(
            brand_name=self.config.brand_name,
            overall_score=overall_score,
            overall_level=self._score_to_level(overall_score),
            twitter_score=twitter_score,
            news_score=news_score,
            total_mentions=len(mentions),
            positive_mentions=positive,
            negative_mentions=negative,
            neutral_mentions=neutral,
            score_change_1h=score_change_1h,
            trending_issues=trending_issues,
        )
        
        self._last_snapshot = snapshot
        return snapshot
    
    def check_alerts(self, snapshot: SentimentSnapshot) -> list[SentimentAlert]:
        """Check if any alerts should be triggered."""
        alerts = []
        
        # Check for negative spike
        if snapshot.overall_score < self.config.alert_threshold_score:
            alert = SentimentAlert(
                id=f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                brand_name=self.config.brand_name,
                severity=AlertSeverity.CRITICAL if snapshot.overall_score < -0.6 else AlertSeverity.WARNING,
                trigger_reason=f"Sentiment dropped to {snapshot.overall_score:.2f}",
                crisis_type=self._detect_crisis_type(snapshot),
                current_score=snapshot.overall_score,
                previous_score=snapshot.overall_score - snapshot.score_change_1h,
                score_change=snapshot.score_change_1h,
                negative_spike_percent=(snapshot.negative_mentions / max(snapshot.total_mentions, 1)) * 100,
                trending_keywords=snapshot.trending_issues,
                recommended_action=self._get_recommended_action(snapshot),
            )
            alerts.append(alert)
            
        # Check for rapid decline
        if snapshot.score_change_1h < self.config.alert_threshold_change:
            alert = SentimentAlert(
                id=f"alert_decline_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                brand_name=self.config.brand_name,
                severity=AlertSeverity.WARNING,
                trigger_reason=f"Rapid sentiment decline: {snapshot.score_change_1h:.2f} in 1 hour",
                current_score=snapshot.overall_score,
                previous_score=snapshot.overall_score - snapshot.score_change_1h,
                score_change=snapshot.score_change_1h,
                recommended_action="Monitor closely for developing situation",
            )
            alerts.append(alert)
            
        return alerts
    
    def _detect_crisis_type(self, snapshot: SentimentSnapshot) -> CrisisType:
        """Attempt to classify the type of crisis based on trending issues."""
        issues_lower = " ".join(snapshot.trending_issues).lower()
        
        if any(kw in issues_lower for kw in ["outage", "down", "broken", "error", "bug"]):
            return CrisisType.SERVICE_OUTAGE
        elif any(kw in issues_lower for kw in ["breach", "hack", "leak", "data"]):
            return CrisisType.DATA_BREACH
        elif any(kw in issues_lower for kw in ["ceo", "founder", "executive", "fired"]):
            return CrisisType.EXECUTIVE_CONTROVERSY
        elif any(kw in issues_lower for kw in ["defect", "recall", "dangerous", "unsafe"]):
            return CrisisType.PRODUCT_ISSUE
        elif any(kw in issues_lower for kw in ["scandal", "lawsuit", "fraud"]):
            return CrisisType.PR_SCANDAL
        else:
            return CrisisType.GENERAL_NEGATIVE
    
    def _get_recommended_action(self, snapshot: SentimentSnapshot) -> str:
        """Generate recommended action based on sentiment state."""
        if snapshot.overall_score < -0.6:
            return "🚨 CRITICAL: Pause all ads immediately. Assess situation before resuming."
        elif snapshot.overall_score < -0.4:
            return "⚠️ Pause promotional ads. Keep informational content running."
        elif snapshot.overall_score < -0.2:
            return "📊 Monitor closely. Consider pausing aggressive sales messaging."
        else:
            return "✅ Continue normal operations. Keep monitoring."
    
    def evaluate_auto_pause(self, snapshot: SentimentSnapshot) -> tuple[bool, Optional[AutoPauseRule]]:
        """Check if any auto-pause rule should trigger."""
        for rule in self.config.auto_pause_rules:
            if rule.evaluate(snapshot):
                return True, rule
        return False, None
    
    async def run_monitoring_cycle(self) -> SentimentReport:
        """Run a complete monitoring cycle."""
        logger.info(f"Starting monitoring cycle for {self.config.brand_name}")
        
        # Fetch mentions from all sources
        all_mentions = []
        
        if self.config.monitor_news:
            news = await self.fetch_news_mentions(self.config.lookback_hours)
            all_mentions.extend(news)
            
        if self.config.monitor_twitter:
            twitter = await self.fetch_twitter_mentions(self.config.lookback_hours)
            all_mentions.extend(twitter)
        
        logger.info(f"Fetched {len(all_mentions)} total mentions")
        
        # Analyze sentiment
        if all_mentions:
            all_mentions = await self.analyze_sentiment_batch(all_mentions)
        
        # Update cache
        self._mentions_cache = all_mentions
        
        # Create snapshot
        snapshot = await self.create_snapshot(all_mentions)
        
        # Check alerts
        alerts = self.check_alerts(snapshot)
        
        # Check auto-pause
        should_pause, triggered_rule = self.evaluate_auto_pause(snapshot)
        
        # Build report
        report = SentimentReport(
            brand_name=self.config.brand_name,
            report_period_hours=self.config.lookback_hours,
            current_snapshot=snapshot,
            health_status=snapshot.get_health_status(),
            active_alerts=alerts,
            most_positive=sorted(
                [m for m in all_mentions if m.sentiment_score > 0.2],
                key=lambda x: x.sentiment_score,
                reverse=True
            )[:3],
            most_negative=sorted(
                [m for m in all_mentions if m.sentiment_score < -0.2],
                key=lambda x: x.sentiment_score
            )[:3],
            most_viral=sorted(
                all_mentions,
                key=lambda x: x.engagement or 0,
                reverse=True
            )[:3],
            key_themes=snapshot.trending_issues,
            recommended_actions=[a.recommended_action for a in alerts] if alerts else ["Continue normal operations"],
            ads_paused=should_pause,
            pause_reason=triggered_rule.id if triggered_rule else None,
            paused_themes=triggered_rule.pause_themes if triggered_rule else [],
        )
        
        logger.info(f"Monitoring cycle complete. Health: {report.health_status}")
        
        return report


# Demo/mock data for testing without API keys
def create_mock_mentions(brand_name: str, scenario: str = "normal") -> list[BrandMention]:
    """Create mock mentions for testing different scenarios."""
    
    base_time = datetime.utcnow()
    
    if scenario == "crisis":
        return [
            BrandMention(
                id="mock_1",
                brand_name=brand_name,
                source=MentionSource.TWITTER,
                content=f"Can't believe {brand_name} is down AGAIN. Third time this week!",
                sentiment_score=-0.8,
                sentiment_level=SentimentLevel.VERY_NEGATIVE,
                confidence=0.9,
                published_at=base_time - timedelta(minutes=30),
                engagement=1500,
                key_phrases=["down again", "third time"],
                detected_issues=["service outage"],
            ),
            BrandMention(
                id="mock_2",
                brand_name=brand_name,
                source=MentionSource.NEWS,
                content=f"{brand_name} faces backlash after major service disruption affects thousands",
                sentiment_score=-0.7,
                sentiment_level=SentimentLevel.VERY_NEGATIVE,
                confidence=0.85,
                published_at=base_time - timedelta(hours=1),
                reach=50000,
                key_phrases=["backlash", "disruption"],
                detected_issues=["service outage", "customer complaints"],
            ),
            BrandMention(
                id="mock_3",
                brand_name=brand_name,
                source=MentionSource.TWITTER,
                content=f"Switching away from {brand_name}. Reliability is non-existent.",
                sentiment_score=-0.6,
                sentiment_level=SentimentLevel.NEGATIVE,
                confidence=0.8,
                published_at=base_time - timedelta(hours=2),
                engagement=800,
                key_phrases=["switching away", "reliability"],
                detected_issues=["churn risk"],
            ),
        ]
    
    elif scenario == "positive":
        return [
            BrandMention(
                id="mock_1",
                brand_name=brand_name,
                source=MentionSource.TWITTER,
                content=f"Just discovered {brand_name} and it's amazing! Best decision ever.",
                sentiment_score=0.9,
                sentiment_level=SentimentLevel.VERY_POSITIVE,
                confidence=0.9,
                published_at=base_time - timedelta(minutes=30),
                engagement=500,
                key_phrases=["amazing", "best decision"],
            ),
            BrandMention(
                id="mock_2",
                brand_name=brand_name,
                source=MentionSource.NEWS,
                content=f"{brand_name} wins industry award for innovation and customer satisfaction",
                sentiment_score=0.8,
                sentiment_level=SentimentLevel.VERY_POSITIVE,
                confidence=0.95,
                published_at=base_time - timedelta(hours=1),
                reach=30000,
                key_phrases=["award", "innovation"],
            ),
        ]
    
    else:  # normal/mixed
        return [
            BrandMention(
                id="mock_1",
                brand_name=brand_name,
                source=MentionSource.TWITTER,
                content=f"Using {brand_name} for my project. Works pretty well so far.",
                sentiment_score=0.3,
                sentiment_level=SentimentLevel.POSITIVE,
                confidence=0.7,
                published_at=base_time - timedelta(minutes=30),
                engagement=50,
                key_phrases=["works well"],
            ),
            BrandMention(
                id="mock_2",
                brand_name=brand_name,
                source=MentionSource.NEWS,
                content=f"{brand_name} announces new features in latest update",
                sentiment_score=0.1,
                sentiment_level=SentimentLevel.NEUTRAL,
                confidence=0.8,
                published_at=base_time - timedelta(hours=1),
                reach=10000,
                key_phrases=["new features", "update"],
            ),
            BrandMention(
                id="mock_3",
                brand_name=brand_name,
                source=MentionSource.TWITTER,
                content=f"Had a minor issue with {brand_name} but support resolved it quickly",
                sentiment_score=-0.1,
                sentiment_level=SentimentLevel.NEUTRAL,
                confidence=0.75,
                published_at=base_time - timedelta(hours=2),
                engagement=30,
                key_phrases=["minor issue", "support"],
                detected_issues=["support ticket"],
            ),
        ]


async def demo_sentiment_monitor(brand_name: str = "Careerfied", scenario: str = "normal"):
    """Demo the sentiment monitor with mock data."""
    
    print(f"\n{'='*60}")
    print(f"🔍 SENTIMENT MONITOR DEMO - {brand_name}")
    print(f"{'='*60}")
    print(f"Scenario: {scenario.upper()}")
    
    # Create config
    config = SentimentMonitorConfig(
        brand_name=brand_name,
        brand_keywords=["career coaching", "AI career"],
        monitor_twitter=False,  # Use mock data
        monitor_news=False,     # Use mock data
        auto_pause_rules=[
            AutoPauseRule(
                id="default_pause",
                brand_name=brand_name,
                min_sentiment_score=-0.4,
                max_negative_percent=50.0,
            )
        ]
    )
    
    monitor = SentimentMonitor(config)
    
    # Use mock mentions
    mentions = create_mock_mentions(brand_name, scenario)
    print(f"\n📊 Analyzing {len(mentions)} mentions...")
    
    # Create snapshot
    snapshot = await monitor.create_snapshot(mentions)
    
    print(f"\n{'─'*40}")
    print(f"SENTIMENT SNAPSHOT")
    print(f"{'─'*40}")
    print(f"Health Status:    {snapshot.get_health_status()}")
    print(f"Overall Score:    {snapshot.overall_score:.2f}")
    print(f"Total Mentions:   {snapshot.total_mentions}")
    print(f"  ├─ Positive:    {snapshot.positive_mentions}")
    print(f"  ├─ Neutral:     {snapshot.neutral_mentions}")
    print(f"  └─ Negative:    {snapshot.negative_mentions}")
    
    if snapshot.trending_issues:
        print(f"\nTrending Issues:  {', '.join(snapshot.trending_issues)}")
    
    # Check alerts
    alerts = monitor.check_alerts(snapshot)
    if alerts:
        print(f"\n{'─'*40}")
        print(f"⚠️  ALERTS ({len(alerts)})")
        print(f"{'─'*40}")
        for alert in alerts:
            print(f"[{alert.severity.value.upper()}] {alert.trigger_reason}")
            print(f"  → {alert.recommended_action}")
    
    # Check auto-pause
    should_pause, rule = monitor.evaluate_auto_pause(snapshot)
    if should_pause:
        print(f"\n{'─'*40}")
        print(f"🛑 AUTO-PAUSE TRIGGERED")
        print(f"{'─'*40}")
        print(f"Rule: {rule.id}")
        print(f"Action: Ads should be paused immediately")
    else:
        print(f"\n✅ No auto-pause triggered - ads can continue running")
    
    print(f"\n{'='*60}\n")
    
    return snapshot, alerts


if __name__ == "__main__":
    # Run demo with different scenarios
    print("\n" + "="*60)
    print("BRANDTRUTH AI - SENTIMENT MONITOR")
    print("Slice 6: Your Unique Differentiator")
    print("="*60)
    
    async def run_demos():
        # Normal scenario
        await demo_sentiment_monitor("Careerfied", "normal")
        
        # Crisis scenario  
        await demo_sentiment_monitor("Careerfied", "crisis")
        
        # Positive scenario
        await demo_sentiment_monitor("Careerfied", "positive")
    
    asyncio.run(run_demos())
