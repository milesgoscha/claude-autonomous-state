#!/usr/bin/env python3
"""
Kalshi Trading MCP Server
Provides Claude with direct access to Kalshi prediction market API
"""

import os
import sys
import json
import time
import base64
import logging
from typing import Any, Optional
from datetime import datetime

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("kalshi-mcp")

# Initialize FastMCP server
mcp = FastMCP("kalshi")

# Configuration
API_BASE_URL = "https://api.elections.kalshi.com"
TRADE_API_BASE = f"{API_BASE_URL}/trade-api/v2"

# Load credentials from environment or files
PRIVATE_KEY_PATH = os.environ.get("KALSHI_PRIVATE_KEY_PATH", "").strip()
API_KEY_PATH = os.environ.get("KALSHI_API_KEY_PATH", "").strip()

# Cached credentials
_private_key = None
_api_key = None

def get_api_key():
    global _api_key
    if _api_key is None:
        if API_KEY_PATH:
            with open(API_KEY_PATH, "r") as f:
                _api_key = f.read().strip()
        else:
            _api_key = os.environ.get("KALSHI_API_KEY", "").strip()
        if not _api_key:
            raise ValueError("KALSHI_API_KEY or KALSHI_API_KEY_PATH must be set")
    return _api_key

def get_private_key():
    global _private_key
    if _private_key is None:
        if not PRIVATE_KEY_PATH:
            raise ValueError("KALSHI_PRIVATE_KEY_PATH not set")
        with open(PRIVATE_KEY_PATH, "rb") as f:
            _private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
    return _private_key


def sign_pss_text(text: str) -> str:
    """Sign text using RSA-PSS and return base64 encoded signature."""
    private_key = get_private_key()
    message = text.encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def get_auth_headers(method: str, path: str) -> dict:
    """Generate authentication headers for Kalshi API request."""
    timestamp_ms = str(int(time.time() * 1000))
    # Remove query params from path for signing
    path_without_query = path.split('?')[0]
    msg_string = timestamp_ms + method + path_without_query
    signature = sign_pss_text(msg_string)

    return {
        "Content-Type": "application/json",
        "KALSHI-ACCESS-KEY": get_api_key(),
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
    }


def api_get(path: str, params: dict = None) -> dict:
    """Make authenticated GET request to Kalshi API."""
    full_path = "/trade-api/v2" + path
    url = TRADE_API_BASE + path
    headers = get_auth_headers("GET", full_path)
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def api_post(path: str, body: dict = None) -> dict:
    """Make authenticated POST request to Kalshi API."""
    full_path = "/trade-api/v2" + path
    url = TRADE_API_BASE + path
    headers = get_auth_headers("POST", full_path)
    response = requests.post(url, headers=headers, json=body or {})
    response.raise_for_status()
    return response.json()


def api_delete(path: str) -> dict:
    """Make authenticated DELETE request to Kalshi API."""
    full_path = "/trade-api/v2" + path
    url = TRADE_API_BASE + path
    headers = get_auth_headers("DELETE", full_path)
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


# ============================================================================
# PORTFOLIO TOOLS
# ============================================================================

@mcp.tool()
def get_balance() -> str:
    """Get current account balance including available cash and portfolio value."""
    try:
        result = api_get("/portfolio/balance")
        # API returns flat structure: {balance: int, portfolio_value: int, updated_ts: int}
        available_balance = result.get("balance", 0) / 100  # Convert cents to dollars
        portfolio_value = result.get("portfolio_value", 0) / 100
        return json.dumps({
            "available_balance": available_balance,
            "portfolio_value": portfolio_value,
            "total_value": available_balance + portfolio_value,
            "raw": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_positions(
    limit: int = 100,
    settlement_status: str = None,
    ticker: str = None
) -> str:
    """
    Get current positions in the portfolio.

    Args:
        limit: Maximum number of positions to return (default 100)
        settlement_status: Filter by status - 'settled' or 'unsettled'
        ticker: Filter by specific market ticker
    """
    try:
        params = {"limit": limit}
        if settlement_status:
            params["settlement_status"] = settlement_status
        if ticker:
            params["ticker"] = ticker

        result = api_get("/portfolio/positions", params)
        positions = result.get("market_positions", [])

        formatted = []
        for pos in positions:
            formatted.append({
                "ticker": pos.get("ticker"),
                "market_title": pos.get("market_title", ""),
                "position": pos.get("position", 0),  # Positive = YES, Negative = NO
                "avg_price": pos.get("average_price_paid", 0) / 100 if pos.get("average_price_paid") else None,
                "realized_pnl": pos.get("realized_pnl", 0) / 100,
                "resting_orders_count": pos.get("resting_orders_count", 0),
            })

        return json.dumps({"positions": formatted, "count": len(formatted)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_orders(
    status: str = None,
    ticker: str = None,
    limit: int = 100
) -> str:
    """
    Get orders from the portfolio.

    Args:
        status: Filter by order status - 'resting', 'canceled', 'executed', 'pending'
        ticker: Filter by specific market ticker
        limit: Maximum number of orders to return
    """
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        if ticker:
            params["ticker"] = ticker

        result = api_get("/portfolio/orders", params)
        orders = result.get("orders", [])

        formatted = []
        for order in orders:
            formatted.append({
                "order_id": order.get("order_id"),
                "ticker": order.get("ticker"),
                "side": order.get("side"),  # 'yes' or 'no'
                "action": order.get("action"),  # 'buy' or 'sell'
                "type": order.get("type"),  # 'limit' or 'market'
                "status": order.get("status"),
                "count": order.get("count"),  # Number of contracts
                "remaining_count": order.get("remaining_count"),
                "price": order.get("yes_price", order.get("no_price", 0)) / 100,
                "created_time": order.get("created_time"),
            })

        return json.dumps({"orders": formatted, "count": len(formatted)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_fills(
    ticker: str = None,
    limit: int = 100
) -> str:
    """
    Get trade execution history (fills).

    Args:
        ticker: Filter by specific market ticker
        limit: Maximum number of fills to return
    """
    try:
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker

        result = api_get("/portfolio/fills", params)
        fills = result.get("fills", [])

        formatted = []
        for fill in fills:
            formatted.append({
                "ticker": fill.get("ticker"),
                "side": fill.get("side"),
                "action": fill.get("action"),
                "count": fill.get("count"),
                "price": fill.get("yes_price", fill.get("no_price", 0)) / 100,
                "created_time": fill.get("created_time"),
                "is_taker": fill.get("is_taker"),
            })

        return json.dumps({"fills": formatted, "count": len(formatted)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# MARKET TOOLS
# ============================================================================

@mcp.tool()
def get_markets(
    status: str = "open",
    series_ticker: str = None,
    event_ticker: str = None,
    limit: int = 25,
    cursor: str = None
) -> str:
    """
    Search and list available markets. Returns concise market summaries.

    Args:
        status: Market status filter - 'open', 'closed', 'settled'
        series_ticker: Filter by series (e.g., 'KXBTC' for Bitcoin markets)
        event_ticker: Filter by event ticker
        limit: Maximum number of markets to return (default 25, max 100)
        cursor: Pagination cursor for next page
    """
    try:
        params = {"limit": min(limit, 100), "status": status}
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if cursor:
            params["cursor"] = cursor

        result = api_get("/markets", params)
        markets = result.get("markets", [])

        formatted = []
        for m in markets:
            # Concise output to avoid token limits
            formatted.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "yes_bid": m.get("yes_bid", 0) / 100 if m.get("yes_bid") else None,
                "yes_ask": m.get("yes_ask", 0) / 100 if m.get("yes_ask") else None,
                "volume": m.get("volume", 0),
            })

        return json.dumps({
            "markets": formatted,
            "count": len(formatted),
            "cursor": result.get("cursor")
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_market(ticker: str) -> str:
    """
    Get detailed information about a specific market.

    Args:
        ticker: The market ticker (e.g., 'PRES-2024-DJT')
    """
    try:
        result = api_get(f"/markets/{ticker}")
        m = result.get("market", {})

        return json.dumps({
            "ticker": m.get("ticker"),
            "title": m.get("title"),
            "subtitle": m.get("subtitle", ""),
            "status": m.get("status"),
            "yes_bid": m.get("yes_bid", 0) / 100 if m.get("yes_bid") else None,
            "yes_ask": m.get("yes_ask", 0) / 100 if m.get("yes_ask") else None,
            "no_bid": m.get("no_bid", 0) / 100 if m.get("no_bid") else None,
            "no_ask": m.get("no_ask", 0) / 100 if m.get("no_ask") else None,
            "last_price": m.get("last_price", 0) / 100 if m.get("last_price") else None,
            "volume": m.get("volume", 0),
            "volume_24h": m.get("volume_24h", 0),
            "open_interest": m.get("open_interest", 0),
            "close_time": m.get("close_time"),
            "expiration_time": m.get("expiration_time"),
            "result": m.get("result"),
            "rules_primary": m.get("rules_primary", ""),
            "event_ticker": m.get("event_ticker"),
            "category": m.get("category"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_orderbook(ticker: str, depth: int = 10) -> str:
    """
    Get the order book for a specific market.

    Args:
        ticker: The market ticker
        depth: Number of price levels to return (default 10)
    """
    try:
        result = api_get(f"/markets/{ticker}/orderbook", {"depth": depth})
        orderbook = result.get("orderbook", {})

        return json.dumps({
            "ticker": ticker,
            "yes_bids": [(level[0] / 100, level[1]) for level in orderbook.get("yes", [])],  # (price, quantity)
            "no_bids": [(level[0] / 100, level[1]) for level in orderbook.get("no", [])],
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_events(
    status: str = None,
    series_ticker: str = None,
    limit: int = 50
) -> str:
    """
    Get events (groups of related markets).

    Args:
        status: Event status filter
        series_ticker: Filter by series
        limit: Maximum number of events to return
    """
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker

        result = api_get("/events", params)
        events = result.get("events", [])

        formatted = []
        for e in events:
            formatted.append({
                "event_ticker": e.get("event_ticker"),
                "title": e.get("title"),
                "subtitle": e.get("subtitle", ""),
                "category": e.get("category"),
                "mutually_exclusive": e.get("mutually_exclusive"),
                "markets_count": len(e.get("markets", [])),
            })

        return json.dumps({"events": formatted, "count": len(formatted)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_event(event_ticker: str) -> str:
    """
    Get detailed information about a specific event and its markets.

    Args:
        event_ticker: The event ticker
    """
    try:
        result = api_get(f"/events/{event_ticker}")
        e = result.get("event", {})
        markets = e.get("markets", [])

        formatted_markets = []
        for m in markets:
            formatted_markets.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "yes_bid": m.get("yes_bid", 0) / 100 if m.get("yes_bid") else None,
                "yes_ask": m.get("yes_ask", 0) / 100 if m.get("yes_ask") else None,
                "last_price": m.get("last_price", 0) / 100 if m.get("last_price") else None,
                "volume": m.get("volume", 0),
            })

        return json.dumps({
            "event_ticker": e.get("event_ticker"),
            "title": e.get("title"),
            "subtitle": e.get("subtitle", ""),
            "category": e.get("category"),
            "mutually_exclusive": e.get("mutually_exclusive"),
            "markets": formatted_markets,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TRADING TOOLS
# ============================================================================

@mcp.tool()
def place_order(
    ticker: str,
    side: str,
    action: str,
    count: int,
    type: str = "limit",
    price: float = None
) -> str:
    """
    Place a new order on a market.

    Args:
        ticker: Market ticker to trade
        side: 'yes' or 'no' - which side of the market
        action: 'buy' or 'sell'
        count: Number of contracts
        type: Order type - 'limit' or 'market'
        price: Limit price in dollars (0.01 to 0.99). Required for limit orders.

    Returns:
        Order confirmation with order_id
    """
    try:
        # Validate inputs
        if side not in ("yes", "no"):
            return json.dumps({"error": "side must be 'yes' or 'no'"})
        if action not in ("buy", "sell"):
            return json.dumps({"error": "action must be 'buy' or 'sell'"})
        if type not in ("limit", "market"):
            return json.dumps({"error": "type must be 'limit' or 'market'"})
        if type == "limit" and price is None:
            return json.dumps({"error": "price required for limit orders"})
        if count <= 0:
            return json.dumps({"error": "count must be positive"})

        body = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": type,
        }

        if type == "limit":
            # Convert price from dollars to cents
            price_cents = int(price * 100)
            if side == "yes":
                body["yes_price"] = price_cents
            else:
                body["no_price"] = price_cents

        result = api_post("/portfolio/orders", body)
        order = result.get("order", {})

        return json.dumps({
            "success": True,
            "order_id": order.get("order_id"),
            "ticker": order.get("ticker"),
            "side": order.get("side"),
            "action": order.get("action"),
            "count": order.get("count"),
            "price": price,
            "status": order.get("status"),
            "created_time": order.get("created_time"),
        }, indent=2)
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        return json.dumps({"error": str(e), "detail": error_detail})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cancel_order(order_id: str) -> str:
    """
    Cancel an open order.

    Args:
        order_id: The order ID to cancel
    """
    try:
        result = api_delete(f"/portfolio/orders/{order_id}")
        return json.dumps({
            "success": True,
            "order_id": order_id,
            "message": "Order canceled successfully"
        }, indent=2)
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        return json.dumps({"error": str(e), "detail": error_detail})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_exchange_status() -> str:
    """Get current exchange status and trading schedule."""
    try:
        result = api_get("/exchange/status")
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Kalshi MCP server...")

    # Verify we can load credentials
    try:
        api_key = get_api_key()
        logger.info(f"API Key: {api_key[:8]}...")
    except Exception as e:
        logger.error(f"Failed to load API key: {e}")
        sys.exit(1)

    try:
        get_private_key()
        logger.info("Private key loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load private key: {e}")
        sys.exit(1)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
