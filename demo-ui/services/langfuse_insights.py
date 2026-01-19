# demo-ui/services/langfuse_insights.py
"""Langfuse Insights Service for User-Facing Analytics.

Queries Langfuse API to provide user-centric metrics for the Chainlit dashboard.
This service acts as a bridge between Langfuse observability data and
user-friendly insights displayed in the chat UI.

Data Flow:
    Langfuse DB → Langfuse API → This Service → Chainlit UI Elements

No separate database needed - we query Langfuse directly and cache results.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
import logging

import httpx

logger = logging.getLogger(__name__)


# ============================================================
# Data Classes for Insights
# ============================================================

@dataclass
class ResponseMetadata:
    """Metadata about a single AI response (shown per-message)."""
    trace_id: str
    latency_ms: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    model: str
    nodes_executed: list[str]
    timestamp: datetime
    cost_usd: float = 0.0
    
    @property
    def latency_display(self) -> str:
        """Human-friendly latency display."""
        if self.latency_ms < 1000:
            return f"{self.latency_ms}ms"
        return f"{self.latency_ms / 1000:.1f}s"
    
    @property
    def tokens_display(self) -> str:
        """Human-friendly token display."""
        return f"{self.total_tokens:,} tokens"
    
    @property
    def cost_display(self) -> str:
        """Human-friendly cost display."""
        if self.cost_usd == 0:
            return "Free (local AI)"
        return f"${self.cost_usd:.4f}"


@dataclass
class DailyActivity:
    """Activity data for a single day (for heatmap)."""
    date: datetime
    interaction_count: int
    total_tokens: int
    avg_latency_ms: int
    
    @property
    def intensity(self) -> int:
        """Activity intensity level 0-4 (like GitHub)."""
        if self.interaction_count == 0:
            return 0
        elif self.interaction_count <= 2:
            return 1
        elif self.interaction_count <= 5:
            return 2
        elif self.interaction_count <= 10:
            return 3
        else:
            return 4


@dataclass 
class UserInsights:
    """Aggregated insights for a user (shown in dashboard)."""
    user_id: str
    total_interactions: int
    total_tokens: int
    total_sessions: int
    avg_latency_ms: int
    first_interaction: datetime | None
    last_interaction: datetime | None
    daily_activity: list[DailyActivity] = field(default_factory=list)
    top_topics: list[str] = field(default_factory=list)
    
    @property
    def active_days(self) -> int:
        """Number of days with at least one interaction."""
        return len([d for d in self.daily_activity if d.interaction_count > 0])
    
    @property
    def streak_days(self) -> int:
        """Current streak of consecutive active days."""
        if not self.daily_activity:
            return 0
        
        streak = 0
        today = datetime.now().date()
        
        for activity in sorted(self.daily_activity, key=lambda x: x.date, reverse=True):
            activity_date = activity.date.date() if isinstance(activity.date, datetime) else activity.date
            expected_date = today - timedelta(days=streak)
            
            if activity_date == expected_date and activity.interaction_count > 0:
                streak += 1
            elif activity_date < expected_date:
                break
                
        return streak


# ============================================================
# Langfuse API Client
# ============================================================

class LangfuseInsightsClient:
    """Client for querying Langfuse API for user insights.
    
    Uses Langfuse's public API to fetch traces, sessions, and metrics.
    API Docs: https://api.reference.langfuse.com/
    """
    
    def __init__(
        self,
        host: str | None = None,
        public_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.host = (host or os.getenv("YONCA_LANGFUSE_HOST", "http://localhost:3001")).rstrip("/")
        self.public_key = public_key or os.getenv("YONCA_LANGFUSE_PUBLIC_KEY", "")
        self.secret_key = secret_key or os.getenv("YONCA_LANGFUSE_SECRET_KEY", "")
        
        self._client: httpx.AsyncClient | None = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Langfuse credentials are configured."""
        return bool(self.public_key and self.secret_key)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                auth=(self.public_key, self.secret_key),
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ─────────────────────────────────────────────────────────
    # Per-Message Metadata
    # ─────────────────────────────────────────────────────────
    
    async def get_trace_metadata(self, trace_id: str) -> ResponseMetadata | None:
        """Get metadata for a specific trace (for per-message display).
        
        Args:
            trace_id: The Langfuse trace ID
            
        Returns:
            ResponseMetadata or None if not found
        """
        if not self.is_configured:
            return None
            
        try:
            client = await self._get_client()
            response = await client.get(f"/api/public/traces/{trace_id}")
            
            if response.status_code != 200:
                logger.warning(f"Trace not found: {trace_id}")
                return None
            
            data = response.json()
            
            # Extract observations for node execution order
            observations = data.get("observations", [])
            nodes = [obs.get("name", "unknown") for obs in observations if obs.get("type") == "SPAN"]
            
            # Calculate totals from observations
            total_input = sum(obs.get("promptTokens", 0) or 0 for obs in observations)
            total_output = sum(obs.get("completionTokens", 0) or 0 for obs in observations)
            total_tokens = sum(obs.get("totalTokens", 0) or 0 for obs in observations)
            total_cost = sum(obs.get("calculatedTotalCost", 0) or 0 for obs in observations)
            
            # Get model from first generation
            model = "unknown"
            for obs in observations:
                if obs.get("type") == "GENERATION" and obs.get("model"):
                    model = obs.get("model")
                    break
            
            # Calculate latency
            start_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            end_time_str = data.get("endTime") or data["timestamp"]
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return ResponseMetadata(
                trace_id=trace_id,
                latency_ms=latency_ms,
                total_tokens=total_tokens or (total_input + total_output),
                input_tokens=total_input,
                output_tokens=total_output,
                model=model,
                nodes_executed=nodes[:5],  # Limit to avoid UI clutter
                timestamp=start_time,
                cost_usd=total_cost,
            )
            
        except Exception as e:
            logger.error(f"Error fetching trace metadata: {e}")
            return None
    
    # ─────────────────────────────────────────────────────────
    # User Dashboard Data
    # ─────────────────────────────────────────────────────────
    
    async def get_user_insights(
        self,
        user_id: str,
        days: int = 90,
    ) -> UserInsights:
        """Get aggregated insights for a user (for dashboard).
        
        Args:
            user_id: The user identifier
            days: Number of days to look back
            
        Returns:
            UserInsights with aggregated metrics
        """
        if not self.is_configured:
            return self._empty_insights(user_id)
        
        try:
            client = await self._get_client()
            
            # Fetch traces for this user
            from_time = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            
            response = await client.get(
                "/api/public/traces",
                params={
                    "userId": user_id,
                    "fromTimestamp": from_time,
                    "limit": 1000,  # Paginate if needed
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch traces for user: {user_id}")
                return self._empty_insights(user_id)
            
            data = response.json()
            traces = data.get("data", [])
            
            if not traces:
                return self._empty_insights(user_id)
            
            # Aggregate by day
            daily_stats: dict[str, dict] = {}
            total_tokens = 0
            total_latency = 0
            sessions = set()
            
            for trace in traces:
                timestamp = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
                date_key = timestamp.strftime("%Y-%m-%d")
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "count": 0,
                        "tokens": 0,
                        "latency_sum": 0,
                    }
                
                daily_stats[date_key]["count"] += 1
                
                # Get token count from observations
                trace_tokens = trace.get("totalTokens", 0) or 0
                daily_stats[date_key]["tokens"] += trace_tokens
                total_tokens += trace_tokens
                
                # Calculate latency
                if trace.get("endTime"):
                    start = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(trace["endTime"].replace("Z", "+00:00"))
                    latency = int((end - start).total_seconds() * 1000)
                    daily_stats[date_key]["latency_sum"] += latency
                    total_latency += latency
                
                # Track sessions
                if trace.get("sessionId"):
                    sessions.add(trace["sessionId"])
            
            # Build daily activity list (fill in missing days)
            daily_activity = []
            current_date = datetime.utcnow().date()
            
            for i in range(days):
                check_date = current_date - timedelta(days=i)
                date_key = check_date.strftime("%Y-%m-%d")
                
                if date_key in daily_stats:
                    stats = daily_stats[date_key]
                    avg_latency = stats["latency_sum"] // max(stats["count"], 1)
                    daily_activity.append(DailyActivity(
                        date=datetime.combine(check_date, datetime.min.time()),
                        interaction_count=stats["count"],
                        total_tokens=stats["tokens"],
                        avg_latency_ms=avg_latency,
                    ))
                else:
                    daily_activity.append(DailyActivity(
                        date=datetime.combine(check_date, datetime.min.time()),
                        interaction_count=0,
                        total_tokens=0,
                        avg_latency_ms=0,
                    ))
            
            # Sort oldest first (for heatmap display)
            daily_activity.reverse()
            
            # Get first and last interaction times
            timestamps = [datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")) for t in traces]
            
            return UserInsights(
                user_id=user_id,
                total_interactions=len(traces),
                total_tokens=total_tokens,
                total_sessions=len(sessions),
                avg_latency_ms=total_latency // max(len(traces), 1),
                first_interaction=min(timestamps) if timestamps else None,
                last_interaction=max(timestamps) if timestamps else None,
                daily_activity=daily_activity,
            )
            
        except Exception as e:
            logger.error(f"Error fetching user insights: {e}")
            return self._empty_insights(user_id)
    
    async def get_session_traces(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get traces for a specific session (for filtering by day).
        
        Args:
            session_id: The session/thread ID
            limit: Maximum traces to return
            
        Returns:
            List of trace summaries
        """
        if not self.is_configured:
            return []
        
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/public/traces",
                params={
                    "sessionId": session_id,
                    "limit": limit,
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get("data", [])
            
        except Exception as e:
            logger.error(f"Error fetching session traces: {e}")
            return []
    
    async def get_traces_for_date(
        self,
        user_id: str,
        date: datetime,
    ) -> list[dict[str, Any]]:
        """Get traces for a specific date (for drill-down).
        
        Args:
            user_id: The user identifier
            date: The date to filter by
            
        Returns:
            List of trace summaries for that day
        """
        if not self.is_configured:
            return []
        
        try:
            client = await self._get_client()
            
            # Create time range for the day
            start_of_day = datetime.combine(date.date(), datetime.min.time())
            end_of_day = start_of_day + timedelta(days=1)
            
            response = await client.get(
                "/api/public/traces",
                params={
                    "userId": user_id,
                    "fromTimestamp": start_of_day.isoformat() + "Z",
                    "toTimestamp": end_of_day.isoformat() + "Z",
                    "limit": 100,
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get("data", [])
            
        except Exception as e:
            logger.error(f"Error fetching traces for date: {e}")
            return []
    
    def _empty_insights(self, user_id: str) -> UserInsights:
        """Create empty insights for when no data is available."""
        return UserInsights(
            user_id=user_id,
            total_interactions=0,
            total_tokens=0,
            total_sessions=0,
            avg_latency_ms=0,
            first_interaction=None,
            last_interaction=None,
            daily_activity=[],
        )


# ============================================================
# Singleton Instance
# ============================================================

_insights_client: LangfuseInsightsClient | None = None


def get_insights_client() -> LangfuseInsightsClient:
    """Get the singleton insights client."""
    global _insights_client
    if _insights_client is None:
        _insights_client = LangfuseInsightsClient()
    return _insights_client


# ============================================================
# Convenience Functions
# ============================================================

async def get_response_metadata(trace_id: str) -> ResponseMetadata | None:
    """Get metadata for displaying under a response."""
    client = get_insights_client()
    return await client.get_trace_metadata(trace_id)


async def get_user_dashboard_data(user_id: str, days: int = 90) -> UserInsights:
    """Get user insights for the dashboard."""
    client = get_insights_client()
    return await client.get_user_insights(user_id, days)


async def get_day_interactions(user_id: str, date: datetime) -> list[dict]:
    """Get interactions for a specific day (drill-down)."""
    client = get_insights_client()
    return await client.get_traces_for_date(user_id, date)
