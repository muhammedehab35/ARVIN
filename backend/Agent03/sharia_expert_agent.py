import os
import asyncio
import json
import re
import requests
import yfinance as yf
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import openai
from openai import OpenAI
from dataclasses import dataclass
from bs4 import BeautifulSoup
import time

@dataclass
class InvestmentInfo:
    """Structure to store investment information"""
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    business_description: Optional[str] = None
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_price: Optional[float] = None
    website: Optional[str] = None
    news: List[Dict] = None

class ShariaExpertAgent:
    """
    Expert Agent in Islamic Finance with research tools
    """
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4"):
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.client = OpenAI(api_key=openai_api_key)
        
        # Sharia knowledge base
        self.sharia_principles = self._load_sharia_knowledge()
        
        # Tools configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        print("🕌 Sharia Expert Agent initialized with research tools")
    
    def _load_sharia_knowledge(self) -> str:
        """
        Comprehensive Sharia knowledge base
        """
        return """
## FUNDAMENTAL PRINCIPLES OF ISLAMIC FINANCE

### 1. RIBA (INTEREST) - STRICTLY FORBIDDEN
- Definition: Predetermined gain without real commercial risk
- Types: Riba al-fadl (interest on exchange), Riba al-nasia (interest on credit)
- Prohibition: Interest-bearing loans, conventional bonds, interest-bearing accounts
- Banks: JPMorgan, Bank of America, Wells Fargo = HARAM

### 2. GHARAR (EXCESSIVE UNCERTAINTY) - FORBIDDEN
- Definition: Speculation with major uncertainty
- Applications: Complex derivatives, excessive short selling
- Tolerance: Minor gharar acceptable (yasir)

### 3. MAYSIR (GAMBLING/SPECULATION) - FORBIDDEN
- Casinos: MGM Resorts, Caesars Entertainment = HARAM
- Lotteries and sports betting
- Pure speculation without economic basis

### 4. FORBIDDEN SECTORS (HARAM)
- Alcohol: Heineken, Budweiser, Diageo
- Pork: Hormel Foods, Tyson Foods (if pork significant)
- Tobacco: Philip Morris, British American Tobacco
- Adult entertainment: Adult entertainment companies
- Offensive weapons: Lockheed Martin (defense acceptable)

### 5. QUANTITATIVE CRITERIA (FINANCIAL SCREENING)
- Debt/capitalization ratio ≤ 33%
- Interest income ≤ 5% of turnover
- Accounts payable ≤ 33% of capitalization
- Interest-bearing cash ≤ 33% of capitalization

### 6. CONFIRMED HALAL COMPANIES
- Technology: Apple, Microsoft, Google, Tesla
- Healthcare: Johnson & Johnson (halal products)
- E-commerce: Amazon (main activity)
- Services: Visa/Mastercard (scholarly debate but generally accepted)

### 7. HALAL ALTERNATIVE INVESTMENTS
- Sukuk (Islamic bonds)
- Compliant Real Estate Investment Trusts (REITs)
- Commodities: Gold, Silver, Oil
- Certified Islamic funds: Amana, Azzad, Wahed
"""

    async def search_company_info(self, query: str) -> Dict[str, Any]:
        """
        Search for company information via different sources
        """
        try:
            print(f"🔍 Searching company info for: {query}")
            
            # 1. Yahoo Finance (if it's a symbol)
            financial_info = await self._get_yahoo_finance_info(query)
            
            # 2. General web search
            web_info = await self._search_web_company_info(query)
            
            # 3. News search
            news_info = await self._search_company_news(query)
            
            # Combine information
            combined_info = {
                "financial_data": financial_info,
                "web_research": web_info,
                "recent_news": news_info,
                "search_query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            return combined_info
            
        except Exception as e:
            print(f"❌ Error searching company info: {e}")
            return {"error": str(e), "query": query}
    
    async def _get_yahoo_finance_info(self, symbol_or_name: str) -> Dict[str, Any]:
        """
        Retrieves financial information via Yahoo Finance
        """
        try:
            # Try as symbol first
            if len(symbol_or_name) <= 5 and symbol_or_name.isalpha():
                ticker = yf.Ticker(symbol_or_name.upper())
            else:
                # Search symbol by name
                ticker = yf.Ticker(symbol_or_name)
            
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return {"error": "No financial data found"}
            
            # Extract key information
            financial_data = {
                "symbol": info.get("symbol"),
                "company_name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "business_summary": info.get("longBusinessSummary"),
                "market_cap": info.get("marketCap"),
                "revenue": info.get("totalRevenue"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "current_price": info.get("currentPrice"),
                "website": info.get("website"),
                "country": info.get("country"),
                "employees": info.get("fullTimeEmployees"),
                "pe_ratio": info.get("trailingPE"),
                "debt_to_equity": info.get("debtToEquity")
            }
            
            # Calculate Sharia ratios
            ratios = self._calculate_sharia_ratios(financial_data)
            financial_data["sharia_ratios"] = ratios
            
            return financial_data
            
        except Exception as e:
            print(f"⚠️ Yahoo Finance error: {e}")
            return {"error": f"Yahoo Finance error: {str(e)}"}
    
    def _calculate_sharia_ratios(self, financial_data: Dict) -> Dict[str, Any]:
        """
        Calculate Sharia-compliant ratios
        """
        try:
            market_cap = financial_data.get("market_cap", 0)
            total_debt = financial_data.get("total_debt", 0)
            total_cash = financial_data.get("total_cash", 0)
            revenue = financial_data.get("revenue", 0)
            
            ratios = {}
            
            # Debt/capitalization ratio
            if market_cap and market_cap > 0:
                debt_ratio = (total_debt / market_cap) * 100 if total_debt else 0
                ratios["debt_to_market_cap"] = {
                    "value": round(debt_ratio, 2),
                    "limit": 33.0,
                    "compliant": debt_ratio <= 33.0
                }
                
                # Cash/capitalization ratio
                cash_ratio = (total_cash / market_cap) * 100 if total_cash else 0
                ratios["cash_to_market_cap"] = {
                    "value": round(cash_ratio, 2),
                    "limit": 33.0,
                    "compliant": cash_ratio <= 33.0
                }
            
            # Note: Interest income requires more detailed data
            ratios["note"] = "Interest income requires detailed financial statement analysis"
            
            return ratios
            
        except Exception as e:
            return {"error": f"Ratio calculation error: {str(e)}"}
    
    async def _search_web_company_info(self, query: str) -> Dict[str, Any]:
        """
        Web search for additional information
        """
        try:
            # DuckDuckGo search (no API key needed)
            search_url = f"https://duckduckgo.com/html/?q={query} company business model activities"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract search results
                results = []
                for result in soup.find_all('div', class_='result')[:3]:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('div', class_='result__snippet')
                    
                    if title_elem and snippet_elem:
                        results.append({
                            "title": title_elem.get_text(strip=True),
                            "url": title_elem.get('href'),
                            "snippet": snippet_elem.get_text(strip=True)
                        })
                
                return {"results": results}
            
            return {"error": "Web search failed"}
            
        except Exception as e:
            print(f"⚠️ Web search error: {e}")
            return {"error": f"Web search error: {str(e)}"}
    
    async def _search_company_news(self, query: str) -> Dict[str, Any]:
        """
        Search for recent company news
        """
        try:
            # News search via DuckDuckGo News
            news_url = f"https://duckduckgo.com/html/?q={query} news&iar=news&df=m"
            
            response = self.session.get(news_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                news_items = []
                for item in soup.find_all('div', class_='news-result')[:5]:
                    title_elem = item.find('a', class_='news-result__title-link')
                    source_elem = item.find('span', class_='news-result__source')
                    date_elem = item.find('span', class_='news-result__date')
                    
                    if title_elem:
                        news_items.append({
                            "title": title_elem.get_text(strip=True),
                            "url": title_elem.get('href'),
                            "source": source_elem.get_text(strip=True) if source_elem else "Unknown",
                            "date": date_elem.get_text(strip=True) if date_elem else "Recent"
                        })
                
                return {"news": news_items}
            
            return {"error": "News search failed"}
            
        except Exception as e:
            print(f"⚠️ News search error: {e}")
            return {"error": f"News search error: {str(e)}"}
    
    async def check_haram_keywords(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for haram keywords in company information
        """
        try:
            haram_keywords = {
                "alcohol": ["alcohol", "beer", "wine", "spirits", "brewery", "distillery"],
                "pork": ["pork", "pig", "swine", "bacon", "ham"],
                "gambling": ["casino", "gambling", "lottery", "betting", "gaming"],
                "tobacco": ["tobacco", "cigarette", "smoking", "nicotine"],
                "adult_entertainment": ["adult entertainment", "pornography", "strip club"],
                "conventional_banking": ["interest", "usury", "conventional banking", "mortgage lending"]
            }
            
            found_issues = {}
            text_to_check = ""
            
            # Gather all text to check
            if isinstance(company_info, dict):
                for key, value in company_info.items():
                    if isinstance(value, str):
                        text_to_check += f" {value}"
                    elif isinstance(value, dict):
                        text_to_check += f" {json.dumps(value)}"
            
            text_to_check = text_to_check.lower()
            
            # Check each category
            for category, keywords in haram_keywords.items():
                found_keywords = [kw for kw in keywords if kw in text_to_check]
                if found_keywords:
                    found_issues[category] = found_keywords
            
            return {
                "haram_indicators_found": found_issues,
                "is_likely_haram": len(found_issues) > 0,
                "risk_level": "HIGH" if len(found_issues) > 2 else "MEDIUM" if len(found_issues) > 0 else "LOW"
            }
            
        except Exception as e:
            return {"error": f"Keyword check error: {str(e)}"}
    
    async def analyze_investment_comprehensive(self, investment_query: str) -> Dict[str, Any]:
        """
        Comprehensive investment analysis with real-time research
        """
        try:
            print(f"🕌 Starting comprehensive Sharia analysis for: {investment_query}")
            
            # 1. Search company information
            company_research = await self.search_company_info(investment_query)
            
            # 2. Check haram keywords
            haram_check = await self.check_haram_keywords(company_research)
            
            # 3. AI analysis based on collected data
            sharia_analysis = await self._analyze_with_ai(investment_query, company_research, haram_check)
            
            # 4. Compile final report
            comprehensive_report = {
                "investment_query": investment_query,
                "research_data": company_research,
                "haram_screening": haram_check,
                "sharia_analysis": sharia_analysis,
                "timestamp": datetime.now().isoformat(),
                "agent_version": "Expert_Sharia_v2.0"
            }
            
            return comprehensive_report
            
        except Exception as e:
            print(f"❌ Comprehensive analysis error: {e}")
            return {
                "status": "error",
                "message": f"Analysis error: {str(e)}",
                "investment_query": investment_query
            }
    
    async def _analyze_with_ai(self, query: str, research_data: Dict, haram_check: Dict) -> Dict[str, Any]:
        """
        AI analysis with all collected data
        """
        try:
            prompt = f"""
You are an Expert Mufti in Islamic Finance, certified by AAOIFI and Al-Azhar University.

SHARIA ANALYSIS REQUEST:
"{query}"

COLLECTED RESEARCH DATA:
{json.dumps(research_data, indent=2, default=str)}

AUTOMATED HARAM SCREENING:
{json.dumps(haram_check, indent=2)}

SHARIA KNOWLEDGE BASE:
{self.sharia_principles}

ANALYSIS MISSION:
1. Complete analysis according to Islamic Sharia principles
2. Use the real-time research data collected
3. Verify both business AND financial compliance
4. Determine status: HALAL ✅, HARAM ❌, or QUESTIONABLE ⚠️
5. Justify with precise references to Islamic principles
6. Propose halal alternatives if necessary

EVALUATION CRITERIA:
- Main activity (>95% halal required)
- Financial ratios (debt/capitalization ≤33%, etc.)
- Interest income (<5% of revenue)
- Forbidden sectors (alcohol, gambling, tobacco, etc.)
- Ethical governance

MANDATORY RESPONSE FORMAT:
## 🕌 SHARIA VERDICT: [HALAL ✅ / HARAM ❌ / QUESTIONABLE ⚠️]

### 📊 BUSINESS ANALYSIS:
[Analysis of main activity based on collected data]

### 💰 FINANCIAL ANALYSIS:
[Sharia ratios, debt, interest income]

### 🔍 AUTOMATED SCREENING:
[Results of haram screening and validation]

### 🤲 ISLAMIC JUSTIFICATION:
[References to hadiths, Quran, and Sharia principles]

### 📈 RESEARCH DATA USED:
[Which sources were used for analysis]

### 💡 HALAL ALTERNATIVES:
[If HARAM/QUESTIONABLE, propose compliant investments]

### 🎯 CONFIDENCE LEVEL: [HIGH/MEDIUM/LOW]
[Based on quality of available data]

### 🔄 RECOMMENDATIONS:
[Additional recommended actions]

Respond in English with precision and religious authority.
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an Expert Mufti in Islamic Finance with access to real-time research tools."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.2
            )
            
            analysis_text = response.choices[0].message.content
            
            # Extract verdict
            verdict = "QUESTIONABLE ⚠️"
            if "HALAL ✅" in analysis_text:
                verdict = "HALAL ✅"
            elif "HARAM ❌" in analysis_text:
                verdict = "HARAM ❌"
            
            # Extract confidence level
            confidence = "MEDIUM"
            if "CONFIDENCE: HIGH" in analysis_text or "HIGH" in analysis_text:
                confidence = "HIGH"
            elif "CONFIDENCE: LOW" in analysis_text or "LOW" in analysis_text:
                confidence = "LOW"
            
            return {
                "status": "success",
                "verdict": verdict,
                "analysis_text": analysis_text,
                "confidence_level": confidence,
                "research_based": True,
                "sources_used": ["Yahoo Finance", "Web Search", "News Search", "Haram Screening", "Sharia Knowledge Base"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI analysis error: {str(e)}"
            }
    
    async def get_halal_alternatives(self, haram_investment: str, sector: str = None) -> Dict[str, Any]:
        """
        Propose halal alternatives with current data search
        """
        try:
            print(f"🔍 Searching halal alternatives for: {haram_investment}")
            
            # Search for alternatives by sector
            if sector:
                sector_alternatives = await self._search_sector_alternatives(sector)
            else:
                sector_alternatives = {}
            
            # Generate alternatives with AI
            ai_alternatives = await self._generate_ai_alternatives(haram_investment, sector_alternatives)
            
            return {
                "status": "success",
                "haram_investment": haram_investment,
                "sector": sector,
                "sector_research": sector_alternatives,
                "ai_recommendations": ai_alternatives,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Alternatives search error: {str(e)}"
            }
    
    async def _search_sector_alternatives(self, sector: str) -> Dict[str, Any]:
        """
        Search for halal alternatives in the same sector
        """
        try:
            # Base of known alternatives
            known_halal_companies = {
                "technology": ["AAPL", "MSFT", "GOOGL", "INTC", "AMD"],
                "healthcare": ["JNJ", "PFE", "ABT", "MDT"],
                "energy": ["TSLA", "FSLR", "NEE"],
                "consumer": ["AMZN", "COST", "WMT"],
                "finance": ["Sukuk alternatives", "Islamic REITs"]
            }
            
            sector_lower = sector.lower()
            alternatives = []
            
            for cat, companies in known_halal_companies.items():
                if cat in sector_lower or sector_lower in cat:
                    alternatives.extend(companies)
            
            # Search for current information on these alternatives
            alternative_info = {}
            for alt in alternatives[:5]:  # Limit to 5 to avoid too many requests
                info = await self._get_yahoo_finance_info(alt)
                if info and "error" not in info:
                    alternative_info[alt] = {
                        "name": info.get("company_name"),
                        "price": info.get("current_price"),
                        "market_cap": info.get("market_cap"),
                        "sector": info.get("sector")
                    }
            
            return {
                "sector": sector,
                "suggested_alternatives": alternatives,
                "alternative_details": alternative_info
            }
            
        except Exception as e:
            return {"error": f"Sector alternatives error: {str(e)}"}
    
    async def _generate_ai_alternatives(self, haram_investment: str, sector_data: Dict) -> Dict[str, Any]:
        """
        Generate alternatives with AI based on research data
        """
        try:
            prompt = f"""
You are an expert Islamic investment advisor.

NON-COMPLIANT INVESTMENT:
"{haram_investment}"

SECTOR RESEARCH:
{json.dumps(sector_data, indent=2, default=str)}

HALAL KNOWLEDGE BASE:
{self.sharia_principles}

MISSION:
1. Propose 7-10 SPECIFIC and PRACTICAL halal alternatives
2. Use the provided research data
3. Include different types of investments
4. Justify each recommendation with Sharia criteria
5. Provide precise symbols/names when possible

REQUIRED FORMAT:
## 💡 RECOMMENDED HALAL ALTERNATIVES

### 📈 DIRECT HALAL STOCKS:
- [Symbol] [Name] - [Sector] - [Sharia Justification]

### 🏢 SUKUK AND ISLAMIC BONDS:
- [Sukuk Name] - [Issuer] - [Approximate Yield]

### 🏘️ ISLAMIC REAL ESTATE:
- [REIT Type or Investment] - [Region] - [Why Halal]

### 💰 CERTIFIED ISLAMIC FUNDS:
- [Fund Name] - [Manager] - [Focus]

### 🌍 HALAL COMMODITIES:
- [Commodity] - [Platform/ETF] - [Justification]

### 🚀 EMERGING OPPORTUNITIES:
- [New halal sectors] - [Growth potential]

Be precise, practical and actionable in your recommendations.
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in halal investments with access to market data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return {
                "status": "success",
                "recommendations": response.choices[0].message.content,
                "based_on_research": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI alternatives error: {str(e)}"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Expert agent status
        """
        return {
            "agent_name": "Sharia Expert Agent",
            "version": "2.0.0",
            "status": "operational",
            "capabilities": {
                "real_time_research": True,
                "yahoo_finance_integration": True,
                "web_search": True,
                "news_monitoring": True,
                "haram_screening": True,
                "sharia_ratio_calculation": True,
                "ai_analysis": True,
                "alternative_suggestions": True
            },
            "tools": [
                "Yahoo Finance API",
                "DuckDuckGo Search",
                "News Aggregation",
                "Keyword Screening",
                "OpenAI Analysis",
                "Financial Ratio Calculator"
            ],
            "model": self.model_name,
            "sharia_knowledge_base": "Comprehensive Islamic Finance Principles"
        }

# Global instance
sharia_expert_agent = None

def initialize_sharia_expert(openai_api_key: str, model_name: str = "gpt-4"):
    """
    Initialize the Sharia expert agent
    """
    global sharia_expert_agent
    sharia_expert_agent = ShariaExpertAgent(openai_api_key, model_name)
    return sharia_expert_agent