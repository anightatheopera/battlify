from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Contestant(BaseModel):
    id: str         # Spotify URL
    title: str
    artist: str
    image_url: Optional[str] = None
    embed_html: Optional[str] = None
    original_url: str
    preview_url: Optional[str] = None

class Match(BaseModel):
    match_id: int
    contestant_a: Contestant
    contestant_b: Optional[Contestant] = None
    votes_a: int = 0
    votes_b: int = 0
    winner_id: Optional[str] = None

class Round(BaseModel):
    round_index: int
    round_name: str
    matches: List[Match]
    end_time: datetime

class Tournament(BaseModel):
    name: str
    voting_duration_minutes: int
    current_round_index: int = 0
    # NEW: Status can be 'draft', 'active', 'completed', 'cancelled'
    status: Literal['draft', 'active', 'completed', 'cancelled'] = 'draft'
    contestants: List[Contestant] = []
    rounds: List[Round] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TournamentCreate(BaseModel):
    name: str
    voting_duration_minutes: int
    urls: List[str]
    
class VoteLog(BaseModel):
    tournament_id: str
    round_index: int
    match_id: int
    voter_ip: str  # IP hash for privacy
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class LoginRequest(BaseModel):
    password: str
    