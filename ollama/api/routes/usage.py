"""
Usage Analytics API Endpoints
Provides detailed usage tracking, cost analysis, and performance metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from datetime import datetime, timedelta
import uuid

from ...repositories import RepositoryFactory, get_repositories

router = APIRouter(
    prefix="/api/v1/usage",
    tags=["usage"],
)


@router.get("/user")
async def get_user_usage(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get comprehensive usage statistics for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        User usage statistics
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        stats = await usage_repo.get_user_stats(user_id, days)
        
        return {
            "period_days": days,
            "period_end": datetime.utcnow().isoformat(),
            "statistics": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")


@router.get("/user/daily")
async def get_user_daily_usage(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get daily usage breakdown for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        Daily usage statistics
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        daily_stats = await usage_repo.get_daily_usage(user_id, days)
        
        # Format as list with date keys
        daily_list = [
            {
                "date": date,
                "requests": stats["requests"],
                "tokens": stats["tokens"],
                "cost": f"${stats['cost']:.4f}",
            }
            for date, stats in sorted(daily_stats.items())
        ]
        
        return {
            "user_id": str(user_id),
            "period_days": days,
            "daily_breakdown": daily_list,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily usage: {str(e)}")


@router.get("/user/tokens")
async def get_user_tokens(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get token usage summary for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        Token usage breakdown
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        input_tokens, output_tokens = await usage_repo.get_user_token_usage(user_id, days)
        
        return {
            "user_id": str(user_id),
            "period_days": days,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {str(e)}")


@router.get("/user/cost")
async def get_user_cost(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get cost summary for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        Cost breakdown
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        total_cost = await usage_repo.get_user_cost(user_id, days)
        avg_cost_per_day = total_cost / days if days > 0 else 0
        
        return {
            "user_id": str(user_id),
            "period_days": days,
            "total_cost": f"${total_cost:.4f}",
            "avg_cost_per_day": f"${avg_cost_per_day:.4f}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost: {str(e)}")


@router.get("/user/performance")
async def get_user_performance(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get performance metrics for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        Performance statistics
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        avg_response_time = await usage_repo.get_average_response_time(user_id, days)
        usage_records = await usage_repo.get_user_usage(user_id, days)
        
        if not usage_records:
            return {
                "user_id": str(user_id),
                "period_days": days,
                "avg_response_time_ms": 0,
                "min_response_time_ms": 0,
                "max_response_time_ms": 0,
                "success_rate": 0.0,
            }
        
        response_times = [u.response_time_ms for u in usage_records]
        successful = len([u for u in usage_records if u.status_code < 400])
        success_rate = (successful / len(usage_records)) * 100 if usage_records else 0
        
        return {
            "user_id": str(user_id),
            "period_days": days,
            "avg_response_time_ms": f"{avg_response_time:.2f}",
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "success_rate": f"{success_rate:.2f}%",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


@router.get("/endpoint/{endpoint}")
async def get_endpoint_usage(
    endpoint: str = Path(..., description="API endpoint"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get usage statistics for a specific endpoint.
    
    Args:
        endpoint: API endpoint path
        days: Number of days to look back
        repos: Repository factory dependency
        
    Returns:
        Endpoint usage statistics
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        stats = await usage_repo.get_endpoint_stats(endpoint, days)
        
        return {
            "period_days": days,
            "statistics": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get endpoint usage: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_usage(
    admin_key: str = Query(..., description="Admin authorization key"),
    days: int = Query(90, ge=1, description="Delete records older than N days"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Delete old usage records for retention policy.
    
    Args:
        admin_key: Admin authorization key
        days: Age threshold in days
        repos: Repository factory dependency
        
    Returns:
        Cleanup result
    """
    try:
        # Verify admin key (in production, use proper auth)
        # This is a placeholder - implement proper admin verification
        from ollama.config import get_settings
        settings = get_settings()
        
        if admin_key != settings.admin_key:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        usage_repo = repos.get_usage_repository()
        
        deleted_count = await usage_repo.delete_old_usage(days)
        
        return {
            "message": f"Deleted {deleted_count} usage records older than {days} days",
            "deleted_count": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/export")
async def export_usage(
    user_id: uuid.UUID = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    format: str = Query("json", description="Export format (json, csv)"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Export usage data for analysis.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        format: Export format
        repos: Repository factory dependency
        
    Returns:
        Exported usage data
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        usage_records = await usage_repo.get_user_usage(user_id, days)
        
        if format == "json":
            return {
                "user_id": str(user_id),
                "period_days": days,
                "export_date": datetime.utcnow().isoformat(),
                "records": [
                    {
                        "endpoint": u.endpoint,
                        "method": u.method,
                        "status_code": u.status_code,
                        "response_time_ms": u.response_time_ms,
                        "input_tokens": u.input_tokens,
                        "output_tokens": u.output_tokens,
                        "cost": str(u.cost),
                        "timestamp": u.created_at.isoformat(),
                    }
                    for u in usage_records
                ],
            }
        
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "endpoint",
                    "method",
                    "status_code",
                    "response_time_ms",
                    "input_tokens",
                    "output_tokens",
                    "cost",
                    "timestamp",
                ]
            )
            
            writer.writeheader()
            for u in usage_records:
                writer.writerow({
                    "endpoint": u.endpoint,
                    "method": u.method,
                    "status_code": u.status_code,
                    "response_time_ms": u.response_time_ms,
                    "input_tokens": u.input_tokens,
                    "output_tokens": u.output_tokens,
                    "cost": str(u.cost),
                    "timestamp": u.created_at.isoformat(),
                })
            
            return {
                "format": "csv",
                "content": output.getvalue(),
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/summary")
async def get_usage_summary(
    user_id: uuid.UUID = Query(..., description="User ID"),
    repos: RepositoryFactory = Depends(get_repositories),
):
    """Get quick usage summary for dashboard.
    
    Args:
        user_id: User ID
        repos: Repository factory dependency
        
    Returns:
        Quick usage summary
    """
    try:
        usage_repo = repos.get_usage_repository()
        
        # Get 30-day stats
        stats_30 = await usage_repo.get_user_stats(user_id, 30)
        
        # Get 7-day stats for comparison
        stats_7 = await usage_repo.get_user_stats(user_id, 7)
        
        # Get today's stats
        stats_1 = await usage_repo.get_user_stats(user_id, 1)
        
        return {
            "user_id": str(user_id),
            "today": {
                "requests": stats_1["total_requests"],
                "tokens": stats_1["total_input_tokens"] + stats_1["total_output_tokens"],
                "cost": f"${stats_1['total_cost']:.4f}",
            },
            "week": {
                "requests": stats_7["total_requests"],
                "tokens": stats_7["total_input_tokens"] + stats_7["total_output_tokens"],
                "cost": f"${stats_7['total_cost']:.4f}",
            },
            "month": {
                "requests": stats_30["total_requests"],
                "tokens": stats_30["total_input_tokens"] + stats_30["total_output_tokens"],
                "cost": f"${stats_30['total_cost']:.4f}",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
