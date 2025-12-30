import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # Import this
from app.routes import admin, voting
from pathlib import Path
import pymongo 

app = FastAPI()

# --- DATABASE REPAIR LOGIC START ---
def fix_broken_urls():
    """
    Runs on startup. Scans MongoDB for broken 'googleusercontent' links
    and replaces them with the official 'open.spotify.com' links.
    """
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("⚠️ Startup Fix Skipped: MONGO_URI not found.")
            return

        client = pymongo.MongoClient(mongo_uri)
        db = client[os.getenv("DB_NAME", "bracket_db")]
        collection = db["tournaments"]
        
        print("🔧 STARTUP: Checking database for broken Spotify URLs...")
        
        tournaments = collection.find({})
        count = 0

        for tourney in tournaments:
            modified = False
            for round_data in tourney.get("rounds", []):
                for match in round_data.get("matches", []):
                    
                    def repair_contestant(c):
                        if not c: return False
                        embed = c.get("embed_html", "")
                        
                        if "googleusercontent.com" in embed:
                            try:
                                part = embed.split("https://open.spotify.com/embed/track/")[1]
                                track_id = part.split("?")[0]
                                
                                correct_embed = (
                                    f'<iframe style="border-radius:12px" '
                                    f'src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0" '
                                    f'width="100%" height="152" frameBorder="0" allowfullscreen="" '
                                    f'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
                                    f'loading="lazy"></iframe>'
                                )
                                c["embed_html"] = correct_embed
                                return True
                            except IndexError:
                                return False
                        return False

                    if repair_contestant(match.get("contestant_a")): modified = True
                    if repair_contestant(match.get("contestant_b")): modified = True

            if modified:
                collection.replace_one({"_id": tourney["_id"]}, tourney)
                count += 1
        
        print(f"✅ Fixed {count} tournaments.")
        client.close()

    except Exception as e:
        print(f"❌ STARTUP FIX FAILED: {e}")

@app.on_event("startup")
async def startup_event():
    fix_broken_urls()
# --- DATABASE REPAIR LOGIC END ---


# Path Configuration
BASE_DIR = Path(__file__).resolve().parent.parent 
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount Frontend Static Assets
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# SET UP TEMPLATES
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# Include API Routes
app.include_router(admin.router, prefix="/api/admin")
app.include_router(voting.router, prefix="/api/vote")

# Handle Favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / "logo.png")

# --- UPDATED ROUTES TO USE TEMPLATES ---

@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/create")
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/manage/{tournament_id}")
async def manage_page(request: Request, tournament_id: str):
    # You can pass variables directly to HTML here if you want!
    return templates.TemplateResponse("manage.html", {"request": request, "tournament_id": tournament_id})

@app.get("/bracket/{tournament_id}")
async def bracket_page(request: Request, tournament_id: str):
    return templates.TemplateResponse("vote.html", {"request": request, "tournament_id": tournament_id})