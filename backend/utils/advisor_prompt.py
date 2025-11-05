import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _fmt_currency(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"


def _fmt_percent(value: float) -> str:
    try:
        return f"{value:.2f}%"
    except Exception:
        return "0.00%"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _compute_totals(holdings: List[Dict[str, Any]]) -> Dict[str, float]:
    total_value = 0.0
    total_cost = 0.0
    for h in holdings:
        shares = _safe_float(h.get("shares"), 0.0)
        purchase_price = _safe_float(h.get("purchase_price"), 0.0)
        current_value = h.get("current_value")
        # Prefer provided current_value; if missing, approximate using purchase_price
        if current_value is None:
            current_value = shares * purchase_price
        current_value = _safe_float(current_value, 0.0)

        total_value += current_value
        total_cost += shares * purchase_price

    overall_gain_loss_pct = 0.0
    if total_cost > 0:
        overall_gain_loss_pct = ((total_value - total_cost) / total_cost) * 100.0

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "overall_gain_loss_pct": overall_gain_loss_pct,
    }


def _top_holdings_by_value(holdings: List[Dict[str, Any]], total_value: float, top_n: int = 3) -> List[str]:
    enriched = []
    for h in holdings:
        ticker = str(h.get("ticker", "UNKNOWN")).upper()
        shares = _safe_float(h.get("shares"), 0.0)
        purchase_price = _safe_float(h.get("purchase_price"), 0.0)
        current_value = h.get("current_value")
        if current_value is None:
            current_value = shares * purchase_price
        value = _safe_float(current_value, 0.0)
        pct = (value / total_value * 100.0) if total_value > 0 else 0.0
        enriched.append((ticker, value, pct))

    enriched.sort(key=lambda x: x[1], reverse=True)
    top = enriched[: top_n]
    return [f"{t} ({_fmt_percent(p)})" for t, _, p in top]


def _sector_exposure(holdings: List[Dict[str, Any]], total_value: float) -> List[str]:
    sector_to_value: Dict[str, float] = {}
    for h in holdings:
        sector = (h.get("sector") or "Unknown").strip() or "Unknown"
        shares = _safe_float(h.get("shares"), 0.0)
        purchase_price = _safe_float(h.get("purchase_price"), 0.0)
        current_value = h.get("current_value")
        if current_value is None:
            current_value = shares * purchase_price
        value = _safe_float(current_value, 0.0)
        sector_to_value[sector] = sector_to_value.get(sector, 0.0) + value

    # Convert to percentage list sorted descending
    items = []
    for sector, value in sector_to_value.items():
        pct = (value / total_value * 100.0) if total_value > 0 else 0.0
        items.append((sector, pct))
    items.sort(key=lambda x: x[1], reverse=True)
    return [f"{sector} ({_fmt_percent(pct)})" for sector, pct in items]


def generate_advisor_prompt(portfolio_data: Dict[str, Any], user_question: str) -> str:
    """
    Build a structured LLM prompt from portfolio data and a user question.

    Expected portfolio_data format:
    {
        "holdings": [
            {
                "ticker": str,
                "shares": float,
                "purchase_price": float,
                "current_value": float,        # optional; if missing, estimated via shares * purchase_price
                "gain_loss": float,            # optional (absolute $); not required for prompt
                "sector": str                  # optional; defaults to 'Unknown'
            },
            ...
        ]
    }
    """
    try:
        holdings = portfolio_data.get("holdings", []) or []
        if not holdings:
            return (
                "Portfolio Summary: No holdings provided. "
                f"Based on this portfolio, {user_question.strip()}"
            )

        totals = _compute_totals(holdings)
        total_value = totals["total_value"]
        overall_gl_pct = totals["overall_gain_loss_pct"]

        top3 = _top_holdings_by_value(holdings, total_value, top_n=3)
        sectors = _sector_exposure(holdings, total_value)

        top3_str = ", ".join(top3) if top3 else "N/A"
        sectors_str = ", ".join(sectors) if sectors else "Unknown"

        summary = (
            "Portfolio Summary: "
            f"Total Value: {_fmt_currency(total_value)}, "
            f"Overall Gain/Loss: {_fmt_percent(overall_gl_pct)}; "
            f"Top Holdings: {top3_str}; "
            f"Sector Exposure: {sectors_str}. "
            f"Based on this portfolio, {user_question.strip()}"
        )
        return summary

    except Exception as e:
        logger.error(f"Failed to generate advisor prompt: {e}")
        # Fail-safe minimal prompt
        return f"Portfolio Summary unavailable. Based on this portfolio, {user_question.strip()}"
