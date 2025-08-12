from pathlib import Path
from datetime import datetime
from openai import OpenAI
from config import settings
from .tools import get_current_stock_price, get_company_info, search_tool
import logging

# --- Logging Setup ---
logger = logging.getLogger("abacus.analysis")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- OpenAI Client ---
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def analyze_with_openai(prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
    """Analysis function using OpenAI GPT-4o directly"""
    try:
        # Prepare messages for OpenAI
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Call OpenAI API
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"OpenAI analysis error: {str(e)}"
        logger.error(error_msg)
        return error_msg

def run_stock_analysis_direct(stock_symbol: str) -> dict:
    """Complete stock analysis using OpenAI GPT-4o"""
    try:
        # --- Input Preparation ---
        stock_symbol = stock_symbol.upper().strip()
        logger.info(f"🚀 Analyzing {stock_symbol} with GPT-4o")
        logger.info(f"📅 Date: {datetime.now().strftime('%m/%d/%Y %H:%M')}")

        # --- STEP 1: Data Collection ---
        logger.info("📊 Collecting financial data...")
        company_info = get_company_info(stock_symbol)
        current_price = get_current_stock_price(stock_symbol)

        # --- STEP 2: News Search ---
        logger.info("📰 Searching for recent news...")
        news_search = search_tool(f"{stock_symbol} recent financial news 2024 2025")

        # --- STEP 3: Financial Analysis ---
        logger.info("🔍 Financial analysis in progress...")
        financial_system_prompt = (
            "You are a senior financial analyst with 20 years of experience in company valuation. "
            "You excel at analyzing financial ratios, evaluating performance, and identifying trends."
        )
        financial_prompt = f"""
        Analyze in depth the financial data for {stock_symbol}:

        COMPANY DATA:
        {company_info}

        CURRENT PRICE: {current_price}

        MISSION: Provide a complete and structured financial analysis including:

        1. **COMPANY OVERVIEW**
           - Business sector and positioning
           - Size and scope (employees, market cap)

        2. **FINANCIAL PERFORMANCE**
           - Profitability ratios analysis (ROE, ROA, margins)
           - Liquidity and solvency ratios
           - Operational efficiency

        3. **VALUATION**
           - Multiples analysis (P/E, P/B, EV/EBITDA)
           - Comparison with sector averages
           - Assessment of price attractiveness

        4. **STRENGTHS AND WEAKNESSES**
           - Identified strengths
           - Areas of concern
           - Competitive comparison

        5. **TRENDS AND OUTLOOK**
           - Historical growth
           - Cash generation
           - Dividend policy

        FORMAT: Professional, objective report with precise figures and nuanced analysis.
        LANGUAGE: English with appropriate financial terminology.
        """
        financial_analysis = analyze_with_openai(financial_prompt, financial_system_prompt, 2500)

        # --- STEP 4: Market Context Analysis ---
        logger.info("📈 Analyzing market context and news...")
        market_system_prompt = (
            "You are a market analyst expert in financial news and impact assessment. "
            "You identify factors that influence stock prices and evaluate their potential impact."
        )
        market_prompt = f"""
        Analyze the impact of news and market context on {stock_symbol}:

        RECENT NEWS:
        {news_search}

        CURRENT PRICE: {current_price}

        REQUIRED ASSESSMENT:

        1. **RECENT MAJOR EVENTS**
           - Published financial results
           - Strategic announcements
           - Management changes

        2. **MARKET SENTIMENT**
           - Investor perception
           - Analyst recommendations
           - Sector trends

        3. **IMPACT ON VALUATION**
           - Identified positive factors
           - Risks and concerns
           - Expected stock price evolution

        4. **FUTURE CATALYSTS**
           - Upcoming events (earnings, launches)
           - Favorable sector trends
           - Growth opportunities

        5. **RISK FACTORS**
           - Company-specific risks
           - Sector and macroeconomic risks
           - Identified warning signals

        FORMAT: Concise, impact-oriented analysis with potential assessment.
        """
        market_analysis = analyze_with_openai(market_prompt, market_system_prompt, 2000)

        # --- STEP 5: Investment Recommendation ---
        logger.info("💡 Generating investment recommendation...")
        recommendation_system_prompt = (
            "You are a certified senior investment advisor with recognized expertise "
            "in portfolio management and asset allocation. You formulate precise and actionable recommendations "
            "based on rigorous fundamental analysis."
        )
        recommendation_prompt = f"""
        Formulate a complete investment recommendation for {stock_symbol}:

        COMPLETE FINANCIAL ANALYSIS:
        {financial_analysis}

        MARKET CONTEXT AND NEWS:
        {market_analysis}

        CURRENT PRICE: {current_price}

        REQUIRED STRUCTURED RECOMMENDATION:

        1. **MAIN RECOMMENDATION**
           - Decision: STRONG BUY / BUY / HOLD / SELL / STRONG SELL
           - Clear 2-3 sentence justification
           - Conviction level (Strong/Moderate/Weak)

        2. **PRICE TARGET**
           - 12-month target price with methodology
           - Range (optimistic/pessimistic scenario)
           - Upside/downside potential in percentage

        3. **RISK/RETURN PROFILE**
           - Risk level: Low / Moderate / High
           - Expected annualized return
           - Anticipated volatility

        4. **INVESTMENT STRATEGY**
           - Recommended time horizon
           - Entry strategy (gradual/lump sum)
           - Take-profit and stop-loss levels
           - Suggested portfolio allocation

        5. **MONITORING POINTS**
           - 3 main positive catalysts to watch
           - 3 major risks to monitor
           - Key performance indicators (KPIs)
           - Important upcoming milestones

        6. **EXECUTIVE SUMMARY**
           - 3-4 sentence synthesis
           - Appropriate investor profile
           - Time perspective

        FORMAT: Professional, precise, actionable recommendation.
        IMPORTANT: Base only on objective data analysis.
        """
        recommendation = analyze_with_openai(recommendation_prompt, recommendation_system_prompt, 2500)

        # --- STEP 6: Save Results ---
        logger.info("💾 Saving results...")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)

        # --- Save Analysis ---
        analysis_content = f"""# Complete Financial Analysis - {stock_symbol}

**Analysis Date:** {datetime.now().strftime('%m/%d/%Y at %H:%M')}  
**Current Price:** {current_price}  

---

## 📊 Fundamental Financial Analysis

{financial_analysis}

---

## 📈 Market Context and News

{market_analysis}

---

## ⚠️ Disclaimer

This analysis is generated by artificial intelligence for informational purposes only. 
It does not constitute personalized financial advice. Always consult a qualified financial 
advisor before making investment decisions.

*Analysis generated by Abacus FinBot - Powered by ABACUS-AI ANALYSIS*
"""
        with open(output_dir / "Analysis.md", "w", encoding="utf-8") as f:
            f.write(analysis_content)

        # --- Save Recommendation ---
        recommendation_content = f"""# Investment Recommendation - {stock_symbol}

**Date:** {datetime.now().strftime('%m/%d/%Y at %H:%M')}  
**Reference Price:** {current_price}

---

{recommendation}

---

## ⚠️ Important Disclaimer

This recommendation is based on automated analysis and does not constitute personalized 
financial advice. Investments involve risk of capital loss. Consult a financial advisor 
before any investment decision.

*Recommendation generated by Abacus FinBot - Powered by ABACUS AI-ANALYSIS*
"""
        with open(output_dir / "Recommendation.md", "w", encoding="utf-8") as f:
            f.write(recommendation_content)

        logger.info(f"✅ Analysis of {stock_symbol} completed successfully!")
        logger.info(f"📁 Results saved in: {output_dir}")

        # --- Return Success Response ---
        return {
            "status": "success",
            "symbol": stock_symbol,
            "analysis": analysis_content,
            "recommendation": recommendation_content,
            "timestamp": datetime.now().isoformat(),
            "model_used": settings.MODEL_NAME,
            "output_directory": str(output_dir)
        }

    except Exception as e:
        error_msg = f"Error during analysis of {stock_symbol}: {str(e)}"
        logger.error(error_msg)
        # --- Return Error Response ---
        return {
            "status": "error",
            "symbol": stock_symbol,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

def get_analysis_results_direct(stock_symbol: str) -> dict:
    """Retrieve analysis results from generated files"""
    try:
        # --- Setup Output Directory and File Paths ---
        output_dir = Path(__file__).parent / "output"
        analysis_file = output_dir / "Analysis.md"
        recommendation_file = output_dir / "Recommendation.md"

        analysis_content = ""
        recommendation_content = ""

        # --- Read Analysis File ---
        if analysis_file.exists():
            with open(analysis_file, "r", encoding="utf-8") as f:
                analysis_content = f.read()
            logger.info(f"✅ Analysis read: {len(analysis_content)} characters")
        else:
            logger.warning(f"⚠️ Analysis file not found: {analysis_file}")

        # --- Read Recommendation File ---
        if recommendation_file.exists():
            with open(recommendation_file, "r", encoding="utf-8") as f:
                recommendation_content = f.read()
            logger.info(f"✅ Recommendation read: {len(recommendation_content)} characters")
        else:
            logger.warning(f"⚠️ Recommendation file not found: {recommendation_file}")

        # --- Return Success Response ---
        return {
            "status": "success",
            "symbol": stock_symbol,
            "analysis": analysis_content,
            "recommendation": recommendation_content,
            "has_analysis": bool(analysis_content),
            "has_recommendation": bool(recommendation_content),
            "files_found": {
                "analysis": analysis_file.exists(),
                "recommendation": recommendation_file.exists()
            }
        }

    except Exception as e:
        error_msg = f"Error reading results: {str(e)}"
        logger.error(error_msg)
        # --- Return Error Response ---
        return {
            "status": "error",
            "symbol": stock_symbol,
            "error": error_msg
        }
