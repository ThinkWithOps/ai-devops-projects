"""Cost Calculator — converts query time into real business cost."""


def calculate_query_cost(
    query_time_seconds: float,
    daily_executions: int,
    avg_dev_hourly_rate: float = 75.0,
    working_days_per_year: int = 250,
) -> dict:
    """
    Calculate the annual developer/compute cost of a slow query.

    Formula:
        time_per_year_hours = (query_time_s * daily_executions * working_days) / 3600
        annual_cost         = time_per_year_hours * hourly_rate

    Returns
    -------
    dict with keys:
        query_time_seconds, daily_executions, time_per_day_seconds,
        time_per_year_hours, annual_cost_usd, monthly_cost_usd,
        daily_cost_usd, hourly_rate_used
    """
    time_per_day_seconds = query_time_seconds * daily_executions
    time_per_year_seconds = time_per_day_seconds * working_days_per_year
    time_per_year_hours = time_per_year_seconds / 3600

    annual_cost = time_per_year_hours * avg_dev_hourly_rate
    monthly_cost = annual_cost / 12
    daily_cost = annual_cost / working_days_per_year

    return {
        "query_time_seconds": query_time_seconds,
        "daily_executions": daily_executions,
        "time_per_day_seconds": round(time_per_day_seconds, 2),
        "time_per_year_hours": round(time_per_year_hours, 2),
        "annual_cost_usd": round(annual_cost, 2),
        "monthly_cost_usd": round(monthly_cost, 2),
        "daily_cost_usd": round(daily_cost, 2),
        "hourly_rate_used": avg_dev_hourly_rate,
    }


def calculate_savings(
    before_seconds: float,
    after_seconds: float,
    daily_executions: int,
    hourly_rate: float = 75.0,
) -> dict:
    """
    Calculate cost savings from optimising a query.

    Returns
    -------
    dict with keys:
        before, after, annual_savings_usd, improvement_pct,
        time_saved_per_day_seconds
    """
    before = calculate_query_cost(before_seconds, daily_executions, hourly_rate)
    after = calculate_query_cost(after_seconds, daily_executions, hourly_rate)

    improvement_pct = (
        ((before_seconds - after_seconds) / before_seconds * 100)
        if before_seconds > 0
        else 0
    )

    return {
        "before": before,
        "after": after,
        "annual_savings_usd": round(
            before["annual_cost_usd"] - after["annual_cost_usd"], 2
        ),
        "improvement_pct": round(improvement_pct, 1),
        "time_saved_per_day_seconds": round(
            before["time_per_day_seconds"] - after["time_per_day_seconds"], 2
        ),
    }
