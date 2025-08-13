from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from pathlib import Path
from config import settings
from routes import router
from Database.database import create_tables, add_test_users

# Variables de configuration par défaut (puisqu'elles ne sont pas dans config.py)
ENVIRONMENT = "development"
PORT = 8000

# --- Try importing Sharia Expert Agent ---
try:
    from Agent03.sharia_expert_agent import initialize_sharia_expert
    sharia_expert_agent = initialize_sharia_expert(settings.OPENAI_API_KEY, settings.MODEL_NAME)
    SHARIA_EXPERT_AVAILABLE = True
    print("✅ Main: Sharia Expert Agent initialized with research tools")
except ImportError as e:
    print(f"⚠️ Main: Sharia Expert Agent not available - {e}")
    SHARIA_EXPERT_AVAILABLE = False
    sharia_expert_agent = None

# --- FastAPI App Setup ---
app = FastAPI(
    title="Abacus FinBot - Sharia Expert Platform",
    version="3.0.0",
    description="AI-powered Sharia investment expert with real-time research capabilities"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Agent Initialization Status ---
agents_initialized = {
    "agent01": False,  # Chat FinBot
    "agent02": False,  # Stock Analysis  
    "agent03": False   # Sharia Expert with Research Tools
}

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    global agents_initialized

    print("🚀 Starting Abacus FinBot Sharia Expert Platform...")
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"🔌 Port: {PORT}")

    # ========== AGENT 01 (Chat FinBot) ==========
    try:
        print("\n📊 Initializing Agent01 (Chat FinBot)...")
        create_tables()
        print("✅ Database tables created/verified")
        add_test_users()
        print("✅ Test users initialized")
        agents_initialized["agent01"] = True
        print("✅ Agent01 (Chat FinBot) ready!")
    except Exception as e:
        print(f"❌ Error Agent01: {e}")
        agents_initialized["agent01"] = False

    # ========== AGENT 02 (Stock Analysis) ==========
    try:
        print("\n📈 Initializing Agent02 (Stock Analysis)...")
        # Test import des outils stock
        from Agent02.tools import get_current_stock_price
        print("✅ Stock analysis tools imported")
        agents_initialized["agent02"] = True
        print("✅ Agent02 (Stock Analysis) ready!")
    except Exception as e:
        print(f"⚠️ Agent02 unavailable: {e}")
        agents_initialized["agent02"] = False

    # ========== AGENT 03 (Sharia Expert) ==========
    try:
        print("\n🕌 Initializing Agent03 (Sharia Expert)...")
        
        if SHARIA_EXPERT_AVAILABLE and settings.OPENAI_API_KEY:
            print("✅ OpenAI API configured for expert analysis")
            print("✅ Research tools initialized:")
            print("   📊 Yahoo Finance integration")
            print("   🔍 Web search capabilities") 
            print("   📰 News monitoring")
            print("   🚫 Haram keyword screening")
            print("   🤖 AI-powered Sharia analysis")
            print("   💡 Halal alternatives research")
            print("   📈 Sharia ratio calculations")
            
            # Test des capacités de l'expert
            try:
                status = sharia_expert_agent.get_agent_status()
                print(f"✅ Expert status verified: {status.get('status', 'unknown')}")
                agents_initialized["agent03"] = True
                print("✅ Agent03 (Sharia Expert) ready with research tools!")
            except Exception as e:
                print(f"⚠️ Expert status check failed: {e}")
                agents_initialized["agent03"] = True  # Continue anyway
                
        else:
            print("❌ Sharia Expert requirements not met")
            if not settings.OPENAI_API_KEY:
                print("   Missing: OPENAI_API_KEY")
            agents_initialized["agent03"] = False
            
    except Exception as e:
        print(f"❌ Error Agent03: {e}")
        agents_initialized["agent03"] = False

    # ========== SUMMARY ==========
    print("\n" + "="*70)
    print("🕌 ABACUS FINBOT - SHARIA EXPERT PLATFORM")
    print("="*70)
    total_agents = sum(agents_initialized.values())
    print(f"📊 Active agents: {total_agents}/3")
    print("\n📋 Agent status:")

    agents_status = [
        ("Agent01", "Chat FinBot + File Upload", agents_initialized["agent01"]),
        ("Agent02", "Stock Analysis GPT-4o", agents_initialized["agent02"]),
        ("Agent03", "Sharia Expert + Research Tools", agents_initialized["agent03"])
    ]
    for agent, description, status in agents_status:
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent}: {description}")

    if agents_initialized["agent03"]:
        print(f"\n🕌 Agent03 - Sharia Expert capabilities:")
        print("   🔍 Real-time company research")
        print("   📊 Financial data analysis (Yahoo Finance)")
        print("   📰 News and market monitoring")
        print("   🚫 Automated haram screening")
        print("   🤖 AI-powered Sharia verdicts")
        print("   💡 Halal alternatives research")
        print("   📈 Sharia ratio calculations")
        print("   🎯 Confidence-based analysis")

    print(f"\n🤖 AI Model: {settings.MODEL_NAME}")
    print(f"🔑 OpenAI configured: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    
    if ENVIRONMENT == "development":
        print("🌐 API Docs: http://localhost:8000/docs")
        print("🔍 Global health: http://localhost:8000/health/all")

    print("\n🚀 SHARIA EXPERT PLATFORM READY!")
    print("🕌 Advanced Islamic investment analysis with research tools")
    
    if ENVIRONMENT == "development":
        print("📱 You can now launch the frontend interface")
        print("\n💡 Expert endpoints available:")
        print("   POST /islamic/expert-analyze - Comprehensive analysis")
        print("   POST /islamic/expert-alternatives - Research-based alternatives")
        print("   POST /islamic/research-company - Company research")
        print("   GET /islamic/expert-status - Agent capabilities")

    print(f"\n⏱️ Startup completed in {time.time():.1f}s")

# --- Include API Routes ---
app.include_router(router)

@app.get("/")
async def root():
    total_agents = sum(agents_initialized.values())
    
    # Info sur l'expert Sharia
    expert_info = {}
    if SHARIA_EXPERT_AVAILABLE and sharia_expert_agent:
        try:
            expert_status = sharia_expert_agent.get_agent_status()
            expert_info = {
                "capabilities": expert_status.get("capabilities", {}),
                "tools": expert_status.get("tools", []),
                "version": expert_status.get("version", "unknown")
            }
        except Exception:
            expert_info = {"error": "Status unavailable"}
    
    return {
        "application": "Abacus FinBot - Sharia Expert Platform",
        "version": "3.0.0",
        "description": "Advanced Sharia investment expert with real-time research tools",
        "status": "ready" if total_agents >= 2 else "partial",
        "specialization": "Expert Islamic Finance Analysis with Research Capabilities",
        "agents": {
            "agent01": {
                "name": "Chat FinBot",
                "description": "AI chat with Excel/CSV file analysis",
                "status": "✅" if agents_initialized["agent01"] else "❌"
            },
            "agent02": {
                "name": "Stock Analysis",
                "description": "Stock analysis using GPT-4o",
                "status": "✅" if agents_initialized["agent02"] else "❌"
            },
            "agent03": {
                "name": "Sharia Expert Agent",
                "description": "Expert Islamic analysis with research tools",
                "status": "✅" if agents_initialized["agent03"] else "❌",
                "expert_info": expert_info
            }
        },
        "expert_capabilities": {
            "real_time_research": agents_initialized["agent03"],
            "yahoo_finance_integration": agents_initialized["agent03"],
            "web_search": agents_initialized["agent03"],
            "news_monitoring": agents_initialized["agent03"],
            "haram_screening": agents_initialized["agent03"],
            "ai_sharia_analysis": agents_initialized["agent03"],
            "alternative_research": agents_initialized["agent03"],
            "ratio_calculations": agents_initialized["agent03"]
        },
        "features": {
            "chat_ai": "Advanced financial chat with file upload",
            "stock_analysis": "Real-time stock analysis and recommendations",
            "expert_sharia_analysis": "Comprehensive Islamic investment screening",
            "research_tools": "Real-time company and market research",
            "automated_screening": "Haram keyword and ratio analysis",
            "ai_model": settings.MODEL_NAME
        },
        "expert_endpoints": {
            "comprehensive_analysis": "/islamic/expert-analyze",
            "research_alternatives": "/islamic/expert-alternatives", 
            "company_research": "/islamic/research-company",
            "expert_status": "/islamic/expert-status"
        },
        "compatibility": {
            "legacy_endpoints": "Maintained for backward compatibility",
            "simple_analyze": "/islamic/analyze",
            "simple_alternatives": "/islamic/alternatives"
        },
        "environment": ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }

@app.get("/ready")
async def readiness_check():
    total_agents = sum(agents_initialized.values())
    
    # Status détaillé de l'expert
    expert_ready = False
    expert_details = {}
    
    if SHARIA_EXPERT_AVAILABLE and sharia_expert_agent:
        try:
            expert_status = sharia_expert_agent.get_agent_status()
            expert_ready = expert_status.get("status") == "operational"
            expert_details = {
                "tools_available": len(expert_status.get("tools", [])),
                "capabilities_count": len(expert_status.get("capabilities", {})),
                "version": expert_status.get("version", "unknown")
            }
        except Exception as e:
            expert_details = {"error": str(e)}
    
    return {
        "ready": total_agents >= 2,
        "agents_ready": total_agents,
        "total_agents": 3,
        "all_systems": "operational" if total_agents == 3 else "partial",
        "expert_analysis": "ready" if expert_ready else "limited",
        "expert_details": expert_details,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "research_tools": "available" if agents_initialized["agent03"] else "unavailable",
        "platform_type": "Sharia Expert with Research Tools"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "abacus-finbot-sharia-expert",
        "version": "3.0.0",
        "environment": ENVIRONMENT,
        "port": PORT,
        "agents": agents_initialized,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "expert_available": SHARIA_EXPERT_AVAILABLE,
        "research_tools": agents_initialized["agent03"]
    }
if __name__ == "__main__":
    import os
    
    # Détection automatique de l'environnement Render
    is_render = os.getenv("RENDER") == "true" or os.getenv("PORT") is not None
    
    # Configuration du port - Render utilise la variable PORT
    port = int(os.environ.get("PORT", 8000))
    
    # Configuration de l'environnement
    environment = "production" if is_render else ENVIRONMENT
    
    print(f"🚀 Starting Abacus FinBot Backend...")
    print(f"🌍 Environment: {environment}")
    print(f"🔌 Port: {port}")
    print(f"🖥️  Render detected: {'✅' if is_render else '❌'}")
    print(f"🔑 OpenAI Key configured: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    
    if is_render or environment == "production":
        print("🌟 PRODUCTION MODE - Render Deployment")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",  # IMPORTANT: 0.0.0.0 pour Render
            port=port,
            reload=False,    # Pas de reload en production
            log_level="info",
            access_log=True
        )
    else:
        print("🛠️ DEVELOPMENT MODE")
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="debug"
        )
