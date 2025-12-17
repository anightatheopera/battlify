from datetime import datetime, timedelta, timezone
from app.models import Round, Match, Contestant
from app.database import get_database
from bson.objectid import ObjectId

db = get_database()

def create_initial_round(contestants: list[Contestant], duration_minutes: int) -> list[Round]:
    # ... (Shuffling and pairing logic remains the same) ...
    import random
    random.shuffle(contestants)
    matches = []
    match_id_counter = 1
    
    for i in range(0, len(contestants), 2):
        player_a = contestants[i]
        player_b = contestants[i+1] if i+1 < len(contestants) else None
        
        matches.append(Match(
            match_id=match_id_counter,
            contestant_a=player_a,
            contestant_b=player_b
        ))
        match_id_counter += 1

    # FIX: Use timezone.utc explicitly
    first_round = Round(
        round_index=0,
        round_name="Round 1",
        matches=matches,
        end_time=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    )
    
    return [first_round]

def process_round_progression(tournament_id: str):
    t = db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    
    # Check status, not just is_active
    if not t or t.get("status") != "active":
        return t

    current_idx = t["current_round_index"]
    current_round = t["rounds"][current_idx]
    
    # FIX: Ensure 'now' is UTC
    now = datetime.now(timezone.utc)
    
    # Handle end_time parsing (Mongo sometimes returns str, sometimes datetime)
    end_time = current_round["end_time"]
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    
    # Ensure end_time has timezone info for comparison
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    if now > end_time:
        # --- TIME IS UP, PROCESS WINNERS ---
        winners = []
        
        for match in current_round["matches"]:
            if match["contestant_b"] is None:
                winners.append(match["contestant_a"])
                match["winner_id"] = match["contestant_a"]["id"]
                continue

            # Tie-breaker: If votes equal, A wins (random shuffle happened at start)
            if match["votes_a"] >= match["votes_b"]:
                winners.append(match["contestant_a"])
                match["winner_id"] = match["contestant_a"]["id"]
            else:
                winners.append(match["contestant_b"])
                match["winner_id"] = match["contestant_b"]["id"]

        # Save the results of the current round
        db.tournaments.update_one(
            {"_id": ObjectId(tournament_id)},
            {"$set": {f"rounds.{current_idx}": current_round}}
        )

        # CHECK IF TOURNAMENT IS OVER (1 Winner left)
        if len(winners) == 1:
            db.tournaments.update_one(
                {"_id": ObjectId(tournament_id)},
                {"$set": {
                    "status": "completed",  # Update Status
                    "is_active": False      # Update Boolean
                }}
            )
            return db.tournaments.find_one({"_id": ObjectId(tournament_id)})

        # CREATE NEXT ROUND
        new_matches = []
        match_id_counter = 1
        for i in range(0, len(winners), 2):
            p_a = winners[i]
            p_b = winners[i+1] if i+1 < len(winners) else None
            new_matches.append({
                "match_id": match_id_counter,
                "contestant_a": p_a,
                "contestant_b": p_b,
                "votes_a": 0,
                "votes_b": 0,
                "winner_id": None
            })
            match_id_counter += 1
            
        new_round = {
            "round_index": current_idx + 1,
            "round_name": f"Round {current_idx + 2}",
            "matches": new_matches,
            "end_time": datetime.now(timezone.utc) + timedelta(minutes=t["voting_duration_minutes"])
        }
        
        db.tournaments.update_one(
            {"_id": ObjectId(tournament_id)},
            {
                "$set": {"current_round_index": current_idx + 1},
                "$push": {"rounds": new_round}
            }
        )
        return db.tournaments.find_one({"_id": ObjectId(tournament_id)})

    return t