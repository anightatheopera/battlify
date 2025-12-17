from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import admin, voting

app = FastAPI()

# Mount Frontend Static Assets
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include API Routes
app.include_router(admin.router, prefix="/api/admin")
app.include_router(voting.router, prefix="/api/vote")

# Frontend Routes
@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

@app.get("/create")
async def create_page():
    return FileResponse('frontend/create.html')

@app.get("/manage/{tournament_id}")
async def manage_page(tournament_id: str):
    return FileResponse('frontend/manage.html')

@app.get("/bracket/{tournament_id}")
async def bracket_page(tournament_id: str):
    return FileResponse('frontend/vote.html')