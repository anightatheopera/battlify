from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import admin, voting
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent 
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

app.include_router(admin.router, prefix="/api/admin")
app.include_router(voting.router, prefix="/api/vote")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(FRONTEND_DIR / "logo.png")

# Frontend Routes
@app.get("/")
async def read_index():
    return FileResponse(FRONTEND_DIR / 'index.html')

@app.get("/create")
async def create_page():
    return FileResponse(FRONTEND_DIR / 'create.html')

@app.get("/manage/{tournament_id}")
async def manage_page(tournament_id: str):
    return FileResponse(FRONTEND_DIR / 'manage.html')

@app.get("/bracket/{tournament_id}")
async def bracket_page(tournament_id: str):
    return FileResponse(FRONTEND_DIR / 'vote.html')