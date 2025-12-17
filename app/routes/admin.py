import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Body
from jose import jwt, JWTError
from app.models import TournamentCreate, Tournament, Contestant, LoginRequest
from app.services.bracket_service import create_initial_round
from app.services.spotify_service import SpotifyService
from app.database import get_database
from bson.objectid import ObjectId

router = APIRouter()
db = get_database()
spotify_service = SpotifyService()

# CONFIG
SITE_ADMIN_PASS = os.getenv("SITE_ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SPOTIFY_CLIENT_SECRET", "fallback_secret_key") # Use an existing secret for signing
ALGORITHM = "HS256"

# --- AUTH HELPERS ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7) # Login lasts 7 days
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
             raise HTTPException(status_code=401, detail="Invalid Role")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

# --- 1. LOGIN ROUTE ---
@router.post("/login")
async def login(payload: LoginRequest):
    if payload.password != SITE_ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Incorrect Password")
    
    token = create_access_token({"role": "admin"})
    return {"access_token": token, "token_type": "bearer"}

# --- 2. PROTECTED ROUTES (Require verify_admin) ---

@router.post("/create")
async def create_tournament(
    payload: TournamentCreate, 
    _: None = Depends(verify_admin) # <--- This protects the route
):
    contestants = []
    for url in payload.urls:
        if "spotify.com" in url: # Loosened check to allow standard spotify links
            new_songs = spotify_service.parse_url(url)
            contestants.extend(new_songs)
    
    unique_contestants = {c.id: c for c in contestants}.values()
    final_contestants = list(unique_contestants)

    new_tournament = Tournament(
        name=payload.name,
        # No admin_secret anymore
        voting_duration_minutes=payload.voting_duration_minutes,
        status="draft",
        contestants=final_contestants,
        rounds=[]
    )

    result = db.tournaments.insert_one(new_tournament.dict())
    return {"tournament_id": str(result.inserted_id), "message": "Draft created."}

@router.post("/{tournament_id}/add-song")
async def add_song(
    tournament_id: str,
    url: str = Body(..., embed=True),
    _: None = Depends(verify_admin)
):
    new_songs = spotify_service.parse_url(url)
    if not new_songs:
        raise HTTPException(status_code=400, detail="Invalid Link")

    for song in new_songs:
        exists = db.tournaments.find_one({"_id": ObjectId(tournament_id), "contestants.id": song.id})
        if not exists:
            db.tournaments.update_one(
                {"_id": ObjectId(tournament_id)},
                {"$push": {"contestants": song.dict()}}
            )
    return {"message": "Songs added"}

@router.post("/{tournament_id}/remove-song")
async def remove_song(
    tournament_id: str,
    song_id: str = Body(..., embed=True),
    _: None = Depends(verify_admin)
):
    db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$pull": {"contestants": {"id": song_id}}}
    )
    return {"message": "Song removed"}

@router.post("/{tournament_id}/start")
async def start_tournament(tournament_id: str, _: None = Depends(verify_admin)):
    t = db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    if not t or t["status"] != "draft":
         raise HTTPException(status_code=400, detail="Cannot start")

    contestants = [Contestant(**c) for c in t["contestants"]]
    if len(contestants) < 2:
        raise HTTPException(status_code=400, detail="Need 2+ songs")

    rounds = create_initial_round(contestants, t["voting_duration_minutes"])

    db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$set": {"status": "active", "rounds": [r.dict() for r in rounds]}}
    )
    return {"message": "Started"}

@router.delete("/{tournament_id}")
async def delete_tournament(tournament_id: str, _: None = Depends(verify_admin)):
    db.tournaments.delete_one({"_id": ObjectId(tournament_id)})
    return {"message": "Deleted"}