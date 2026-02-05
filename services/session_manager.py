import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from models.game_state import GameState
from utils.logger import get_logger

session_logger = get_logger("session")

class SessionManager:
    """Manages game sessions with TTL and cleanup"""
    
    def __init__(self, ttl_minutes: int = 60, max_sessions: int = 1000):
        self.sessions: Dict[str, Dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_sessions = max_sessions
        
        session_logger.info(
            "Session manager initialized",
            extra={
                "ttl_minutes": ttl_minutes,
                "max_sessions": max_sessions,
                "event": "session_manager_init"
            }
        )
    
    def create_session(self, game_state: GameState) -> str:
        """Create a new game session and return session ID"""
        # Cleanup if approaching max sessions
        if len(self.sessions) >= self.max_sessions * 0.9:
            self.cleanup_expired()
        
        session_id = secrets.token_urlsafe(16)
        
        self.sessions[session_id] = {
            "state": game_state,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow()
        }
        
        session_logger.info(
            "Session created",
            extra={
                "session_id": session_id,
                "player_name": game_state.player_name,
                "total_sessions": len(self.sessions),
                "event": "session_created"
            }
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[GameState]:
        """Get session state and update last accessed time"""
        if session_id not in self.sessions:
            session_logger.warning(
                "Session not found",
                extra={
                    "session_id": session_id,
                    "event": "session_not_found"
                }
            )
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if datetime.utcnow() - session["last_accessed"] > self.ttl:
            session_logger.info(
                "Session expired",
                extra={
                    "session_id": session_id,
                    "last_accessed": session["last_accessed"].isoformat(),
                    "event": "session_expired"
                }
            )
            del self.sessions[session_id]
            return None
        
        # Update last accessed
        session["last_accessed"] = datetime.utcnow()
        
        return session["state"]
    
    def update_session(self, session_id: str, game_state: GameState) -> bool:
        """Update session state"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["state"] = game_state
        self.sessions[session_id]["last_accessed"] = datetime.utcnow()
        
        session_logger.debug(
            "Session updated",
            extra={
                "session_id": session_id,
                "event": "session_updated"
            }
        )
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
            session_logger.info(
                "Session deleted",
                extra={
                    "session_id": session_id,
                    "remaining_sessions": len(self.sessions),
                    "event": "session_deleted"
                }
            )
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions and return count removed"""
        now = datetime.utcnow()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if now - session["last_accessed"] > self.ttl
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]
        
        if expired_sessions:
            session_logger.info(
                "Expired sessions cleaned up",
                extra={
                    "sessions_removed": len(expired_sessions),
                    "remaining_sessions": len(self.sessions),
                    "event": "cleanup_completed"
                }
            )
        
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """Get current number of active sessions"""
        return len(self.sessions)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists and is not expired"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if datetime.utcnow() - session["last_accessed"] > self.ttl:
            del self.sessions[session_id]
            return False
        
        return True