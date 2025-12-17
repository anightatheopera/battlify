from fastapi import APIRouter, HTTPException, Request
from app.database import get_database
from app.models import VoteLog
from app.services.bracket_service import process_round_progression
from bson.objectid import ObjectId
import hashlib

router = APIRouter()
db = get_database()

@router.get("/tournaments")
async def get_active_tournaments():
    tournaments = list(db.tournaments.find(
        {"status": {"$in": ["active", "completed"]}},
        {"_id": 1, "name": 1, "status": 1}
    ))
    for t in tournaments:
        t["_id"] = str(t["_id"])
    return tournaments

@router.get("/tournament/{tournament_id}")
async def get_tournament_bracket(tournament_id: str):
    t = process_round_progression(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    t["_id"] = str(t["_id"])
    return t

@router.post("/vote/{tournament_id}/{match_id}/{option}")
def cast_vote(tournament_id: str, match_id: int, option: str, request: Request):
    if option not in ['a', 'b']:
        raise HTTPException(status_code=400, detail="Invalid option")

    # 1. Get User IP
    client_ip = request.client.host
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers.get("x-forwarded-for")
    voter_hash = hashlib.sha256(client_ip.encode()).hexdigest()

    # 2. GET TOURNAMENT
    t = db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    
    if not t or t.get("status") != "active":
        raise HTTPException(status_code=404, detail="Tournament not found or ended")
    
    current_idx = t["current_round_index"]
    
    # 3. CHECK FOR DUPLICATE VOTE (FIXED)
    # We now check round_index AND match_id
    existing_vote = db.vote_logs.find_one({
        "tournament_id": tournament_id,
        "round_index": current_idx,  # <--- ADDED THIS CHECK
        "match_id": match_id,
        "voter_ip": voter_hash
    })

    if existing_vote:
        raise HTTPException(status_code=403, detail="You have already voted on this match.")

    # 4. INCREMENT VOTE
    field_to_inc = f"rounds.{current_idx}.matches.$[elem].votes_{option}"
    
    result = db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$inc": {field_to_inc: 1}},
        array_filters=[{"elem.match_id": match_id}]
    )
    
    if result.modified_count == 0:
         raise HTTPException(status_code=400, detail="Vote failed. Match might not exist in the current round.")

    # 5. LOG THE VOTE
    db.vote_logs.insert_one({
        "tournament_id": tournament_id,
        "round_index": current_idx,
        "match_id": match_id,
        "voter_ip": voter_hash
    })

    return {"message": "Vote counted"}