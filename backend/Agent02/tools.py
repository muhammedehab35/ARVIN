import json
import os
import time
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

# --- Optional Dependency Management ---
try:
    from curl_cffi import requests
    session = requests.Session(impersonate="chrome")
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    session = requests.Session()
    CURL_CFFI_AVAILABLE = False

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    import openai
    from openai import OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        OPENAI_AVAILABLE = True
    else:
        OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False

# --- DuckDuckGo Search Tool ---
def search_tool(search_query: str) -> str:
    """
    Search for information on the internet using DuckDuckGo.
    Returns a formatted string of results or an error message.
    """
    if not DDGS_AVAILABLE:
        return f"Search not available for: {search_query}"
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(search_query, max_results=5):
                results.append(f"Title: {r['title']}\nSummary: {r['body']}\nURL: {r['href']}\n")
            return "\n---\n".join(results) if results else f"No results found for: {search_query}"
    except Exception as e:
        return f"Search error for '{search_query}': {str(e)}"

# --- Stock Price Retrieval ---
def get_current_stock_price(symbol: str) -> str:
    """
    Get the current stock price for a given symbol.
    Returns price and currency or an error message.
    """
    try:
        time.sleep(0.5)
        stock = yf.Ticker(symbol, session=session) if CURL_CFFI_AVAILABLE else yf.Ticker(symbol)
        info = stock.info
        current_price = info.get("regularMarketPrice") or info.get("currentPrice")
        currency = info.get("currency", "USD")
        if current_price:
            return f"{current_price:.2f} {currency}"
        else:
            return f"Price not available for {symbol}"
    except Exception as e:
        return f"Error retrieving price for {symbol}: {str(e)}"

# --- Company Info Retrieval ---
def get_company_info(symbol: str) -> str:
    """
    Get complete company information for a given symbol.
    Returns a JSON string of cleaned info or an error message.
    """
    try:
        stock = yf.Ticker(symbol, session=session) if CURL_CFFI_AVAILABLE else yf.Ticker(symbol)
        company_info_full = stock.info
        if not company_info_full:
            return f"Information not available for {symbol}"

        # Cleaned and structured information
        company_info_cleaned = {
            "Name": company_info_full.get("shortName") or company_info_full.get("longName"),
            "Symbol": company_info_full.get("symbol"),
            "Current_Price": f"{company_info_full.get('regularMarketPrice', company_info_full.get('currentPrice', 'N/A'))} {company_info_full.get('currency', 'USD')}",
            "Market_Cap": company_info_full.get("marketCap"),
            "Sector": company_info_full.get("sector"),
            "Industry": company_info_full.get("industry"),
            "Country": company_info_full.get("country"),
            "City": company_info_full.get("city"),
            # Financial metrics
            "EPS": company_info_full.get("trailingEps"),
            "PE_Ratio": company_info_full.get("trailingPE"),
            "52W_Low": company_info_full.get("fiftyTwoWeekLow"),
            "52W_High": company_info_full.get("fiftyTwoWeekHigh"),
            "50D_Average": company_info_full.get("fiftyDayAverage"),
            "200D_Average": company_info_full.get("twoHundredDayAverage"),
            # Advanced financial information
            "Employees": company_info_full.get("fullTimeEmployees"),
            "Total_Cash": company_info_full.get("totalCash"),
            "Free_Cash_Flow": company_info_full.get("freeCashflow"),
            "Operating_Cash_Flow": company_info_full.get("operatingCashflow"),
            "EBITDA": company_info_full.get("ebitda"),
            "Revenue_Growth": company_info_full.get("revenueGrowth"),
            "Gross_Margins": company_info_full.get("grossMargins"),
            "EBITDA_Margins": company_info_full.get("ebitdaMargins"),
            "ROE": company_info_full.get("returnOnEquity"),
            "ROA": company_info_full.get("returnOnAssets"),
            # Dividend information
            "Dividend_Yield": company_info_full.get("dividendYield"),
            "Dividend_Rate": company_info_full.get("dividendRate"),
            # Valuation
            "PB_Ratio": company_info_full.get("priceToBook"),
            "PS_Ratio": company_info_full.get("priceToSalesTrailing12Months"),
            "EV_EBITDA": company_info_full.get("enterpriseToEbitda"),
        }
        return json.dumps(company_info_cleaned, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error retrieving info for {symbol}: {str(e)}"

# --- Financial Statements Retrieval ---
def get_income_statements(symbol: str) -> str:
    """
    Get company financial statements for a given symbol.
    Returns JSON string or error message.
    """
    try:
        stock = yf.Ticker(symbol, session=session) if CURL_CFFI_AVAILABLE else yf.Ticker(symbol)
        financials = stock.financials
        if financials.empty:
            return f"Financial statements not available for {symbol}"
        return financials.to_json(orient="index")
    except Exception as e:
        return f"Error retrieving financial statements for {symbol}: {str(e)}"