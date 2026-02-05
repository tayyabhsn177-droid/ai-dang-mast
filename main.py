# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.game_state import GameState
from utils.logger import init_logging, get_logger

# Initialize logging first
init_logging()

from graph_builder import build_graph

app = FastAPI(title="AI Dungeon Master", version="1.0")

# Initialize logger
api_logger = get_logger("api")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build graphs
graph, action_only_graph, next_turn_graph = build_graph()

# Simple in-memory session storage
game_sessions = {}


# ============================================================================
# REQUEST/RESPONSE MODELS (Simplified)
# ============================================================================

class StartGameRequest(BaseModel):
    """Simple request to start a new game"""
    player_name: str
    character_class: str = "Warrior"
    setting: str = "Dark Fantasy Medieval Kingdom"

class ActionRequest(BaseModel):
    """Simple request to take an action"""
    action: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """API Welcome"""
    return {
        "message": "Welcome to AI Dungeon Master!",
        "endpoints": {
            "POST /game/start": "Start a new game",
            "POST /game/{session_id}/action": "Take an action",
            "GET /game/{session_id}": "Get current game state"
        }
    }


@app.post("/game/start")
def start_game(request: StartGameRequest):
    """
    Start a new game session.
    
    Request body:
    {
        "player_name": "YourName",
        "character_class": "Warrior",  // optional, defaults to Warrior
        "setting": "Dark Fantasy"      // optional
    }
    """
    import uuid
    session_id = str(uuid.uuid4())[:8]  # Short session ID
    
    api_logger.info(f"Starting new game for {request.player_name}, session: {session_id}")
    
    # Create minimal initial state
    initial_state = GameState(
        player_name=request.player_name,
        character_class=request.character_class,
        setting=request.setting,
        game_started=False
    )
    
    # Run the initial game graph
    result = graph.invoke(initial_state)
    
    # Convert dict to GameState if needed
    if isinstance(result, dict):
        game_state = GameState(**result)
    else:
        game_state = result
    
    # Store session
    game_sessions[session_id] = game_state
    
    api_logger.info(f"Game started successfully for session {session_id}")
    
    return {
        "session_id": session_id,
        "message": f"Welcome, {request.player_name}!",
        "world_intro": game_state.world_intro,
        "current_scene": game_state.current_scene,
        "available_actions": game_state.available_actions,
        "player_stats": {
            "hp": game_state.health_points,
            "max_hp": game_state.max_health_points,
            "level": game_state.level,
            "inventory": game_state.inventory
        }
    }


@app.post("/game/{session_id}/action")
def take_action(session_id: str, request: ActionRequest):
    """
    Take an action in your game.
    
    Request body:
    {
        "action": "Explore the cave"
    }
    
    Returns updated game state with new scene and actions.
    """
    # Check if session exists
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    current_state = game_sessions[session_id]
    
    # Check if game is over
    if current_state.health_points <= 0:
        return {
            "game_over": True,
            "message": "You have fallen! Your journey ends here.",
            "final_stats": {
                "level": current_state.level,
                "experience": current_state.experience_points,
                "inventory": current_state.inventory
            }
        }
    
    api_logger.info(f"Session {session_id}: Player action: {request.action}")
    
    # Update state with selected action
    current_state.selected_action = request.action
    
    # Run action resolution
    result = action_only_graph.invoke(current_state)
    
    # Convert to GameState
    if isinstance(result, dict):
        new_state = GameState(**result)
    else:
        new_state = result
    
    # Update session
    game_sessions[session_id] = new_state
    
    # Check for game over
    if new_state.health_points <= 0:
        api_logger.info(f"Game over for session {session_id}")
        return {
            "game_over": True,
            "message": "You have fallen! Your journey ends here.",
            "death_scene": new_state.current_scene,
            "final_stats": {
                "level": new_state.level,
                "experience": new_state.experience_points,
                "inventory": new_state.inventory
            }
        }
    
    # Return simplified response for continuous play
    return {
        "session_id": session_id,
        "current_scene": new_state.current_scene,
        "available_actions": new_state.available_actions,
        "dice_roll": new_state.last_dice_roll,
        "outcome": new_state.last_roll_outcome,
        "player_stats": {
            "hp": new_state.health_points,
            "max_hp": new_state.max_health_points,
            "level": new_state.level,
            "xp": new_state.experience_points,
            "inventory": new_state.inventory
        }
    }


@app.get("/game/{session_id}")
def get_game_state(session_id: str):
    """Get the current state of your game"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    state = game_sessions[session_id]
    
    return {
        "session_id": session_id,
        "player_name": state.player_name,
        "character_class": state.character_class,
        "current_scene": state.current_scene,
        "available_actions": state.available_actions,
        "player_stats": {
            "hp": state.health_points,
            "max_hp": state.max_health_points,
            "level": state.level,
            "xp": state.experience_points,
            "inventory": state.inventory
        },
        "quest_info": {
            "main_quest": state.main_quest,
            "side_quests": state.side_quests
        },
        "game_over": state.health_points <= 0
    }


@app.delete("/game/{session_id}")
def end_game(session_id: str):
    """End your game session"""
    if session_id in game_sessions:
        del game_sessions[session_id]
        api_logger.info(f"Session {session_id} deleted")
        return {"message": "Game session ended"}
    raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


# uvicorn main:app --reload