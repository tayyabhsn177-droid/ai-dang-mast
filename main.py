# main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from models.game_state import GameState, AttributeType
from utils.logger import init_logging, get_logger
from services.session_manager import SessionManager
from typing import Optional
import asyncio
from models.enemy import spawn_random_enemy, create_dragon_boss, create_necromancer, create_orc, create_goblin
from services.combat_system import CombatSystem


# Initialize logging first
init_logging()

from graph_builder import build_graph

app = FastAPI(
    title="AI Dungeon Master", 
    version="2.0",
    description="AI-powered text RPG with dynamic storytelling"
)

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
graph, action_only_graph = build_graph()

# Session manager (60 min TTL, max 1000 sessions)
session_manager = SessionManager(ttl_minutes=60, max_sessions=1000)

combat_systems = {}  # session_id -> CombatSystem


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartGameRequest(BaseModel):
    """Request to start a new game"""
    player_name: str = Field(..., min_length=1, max_length=50, description="Player's name")
    character_class: str = Field(default="Warrior", description="Character class")
    setting: str = Field(default="Dark Fantasy Medieval Kingdom", description="Game setting/theme")


class ActionRequest(BaseModel):
    """Request to take an action"""
    action: str = Field(..., min_length=1, description="Action to perform")


class AttributeSpendRequest(BaseModel):
    """Request to spend attribute points"""
    attribute: AttributeType = Field(..., description="Attribute to increase")


# Background task for session cleanup
async def cleanup_sessions_task():
    """Periodically cleanup expired sessions"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        removed = session_manager.cleanup_expired()
        if removed > 0:
            api_logger.info(
                f"Background cleanup removed {removed} expired sessions",
                extra={"sessions_removed": removed, "event": "background_cleanup"}
            )


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(cleanup_sessions_task())
    api_logger.info("Server started, background tasks initialized")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """API Welcome"""
    return {
        "message": "Welcome to AI Dungeon Master v2.0!",
        "endpoints": {
            "POST /game/start": "Start a new game",
            "POST /game/{session_id}/action": "Take an action",
            "GET /game/{session_id}": "Get current game state",
            "GET /game/{session_id}/character": "View character sheet",
            "POST /game/{session_id}/attribute": "Spend attribute points",
            "DELETE /game/{session_id}": "End game session"
        },
        "active_sessions": session_manager.get_session_count()
    }


@app.post("/game/start")
def start_game(request: StartGameRequest):
    """
    Start a new game session.
    
    Creates a character and generates the initial world/quest.
    """
    api_logger.info(
        f"Starting new game for {request.player_name}",
        extra={
            "player_name": request.player_name,
            "character_class": request.character_class,
            "event": "game_start_request"
        }
    )
    
    try:
        # Create initial state
        initial_state = GameState(
            player_name=request.player_name,
            character_class=request.character_class,
            setting=request.setting,
            game_started=False
        )
        
        # CRITICAL FIX: Initialize character stats properly
        initial_state.update_character_stats()
        
        # Run the initial game graph
        result = graph.invoke(initial_state)
        
        # Convert dict to GameState if needed
        if isinstance(result, dict):
            game_state = GameState(**result)
        else:
            game_state = result
        
        # Store session
        session_id = session_manager.create_session(game_state)
        
        api_logger.info(
            f"Game started successfully for session {session_id}",
            extra={
                "session_id": session_id,
                "player_name": request.player_name,
                "event": "game_started"
            }
        )
        
        return {
            "session_id": session_id,
            "message": f"Welcome, {request.player_name}!",
            "world_intro": game_state.world_intro,
            "current_scene": game_state.current_scene,
            "available_actions": game_state.available_actions,
            "player_stats": {
                "hp": game_state.character_stats.health_points,
                "max_hp": game_state.character_stats.max_health_points,
                "mana": game_state.character_stats.mana_points,
                "max_mana": game_state.character_stats.max_mana_points,
                "stamina": game_state.character_stats.stamina_points,
                "max_stamina": game_state.character_stats.max_stamina_points,
                "level": game_state.character_stats.level,
                "xp": game_state.character_stats.experience_points,
                "xp_to_next": game_state.character_stats.experience_to_next_level,
                "inventory": game_state.inventory
            }
        }
    
    except Exception as e:
        api_logger.error(
            f"Failed to start game: {str(e)}",
            exc_info=True,
            extra={"error_type": type(e).__name__, "event": "game_start_failed"}
        )
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")


@app.post("/game/{session_id}/action")
def take_action(session_id: str, request: ActionRequest):
    """
    Take an action in your game.
    
    Validates the action, rolls dice with attribute modifiers, 
    resolves consequences, and returns updated game state.
    """
    # Check if session exists
    current_state = session_manager.get_session(session_id)
    if not current_state:
        raise HTTPException(
            status_code=404, 
            detail=f"Session {session_id} not found or expired"
        )
    
    # Check if game is over
    if current_state.character_stats.health_points <= 0:
        api_logger.info(f"Attempted action on dead character in session {session_id}")
        return {
            "game_over": True,
            "message": "You have fallen! Your journey ends here.",
            "final_stats": {
                "level": current_state.character_stats.level,
                "experience": current_state.character_stats.experience_points,
                "inventory": current_state.inventory
            }
        }
    
    # Validate action is in available actions (optional but recommended)
    if request.action not in current_state.available_actions:
        api_logger.warning(
            f"Action '{request.action}' not in available actions",
            extra={
                "session_id": session_id,
                "action": request.action,
                "available_actions": current_state.available_actions,
                "event": "invalid_action"
            }
        )
        # Allow it anyway for flexibility, but log it
    
    api_logger.info(
        f"Session {session_id}: Player action: {request.action}",
        extra={
            "session_id": session_id,
            "action": request.action,
            "event": "action_request"
        }
    )
    
    try:
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
        session_manager.update_session(session_id, new_state)
        
        # Check for game over
        if new_state.character_stats.health_points <= 0:
            api_logger.info(f"Game over for session {session_id}")
            return {
                "game_over": True,
                "message": "You have fallen! Your journey ends here.",
                "death_scene": new_state.current_scene,
                "final_stats": {
                    "level": new_state.character_stats.level,
                    "experience": new_state.character_stats.experience_points,
                    "inventory": new_state.inventory
                }
            }
        
        # Return detailed response
        return {
            "session_id": session_id,
            "current_scene": new_state.current_scene,
            "available_actions": new_state.available_actions,
            "dice_roll": new_state.last_dice_roll,
            "outcome": new_state.last_roll_outcome,
            "player_stats": {
                "hp": new_state.character_stats.health_points,
                "max_hp": new_state.character_stats.max_health_points,
                "mana": new_state.character_stats.mana_points,
                "max_mana": new_state.character_stats.max_mana_points,
                "stamina": new_state.character_stats.stamina_points,
                "max_stamina": new_state.character_stats.max_stamina_points,
                "level": new_state.character_stats.level,
                "xp": new_state.character_stats.experience_points,
                "xp_to_next": new_state.character_stats.experience_to_next_level,
                "inventory": new_state.inventory
            }
        }
    
    except Exception as e:
        api_logger.error(
            f"Failed to process action: {str(e)}",
            exc_info=True,
            extra={
                "session_id": session_id,
                "action": request.action,
                "error_type": type(e).__name__,
                "event": "action_failed"
            }
        )
        raise HTTPException(status_code=500, detail=f"Failed to process action: {str(e)}")


@app.get("/game/{session_id}")
def get_game_state(session_id: str):
    """Get the current state of your game"""
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=404, 
            detail=f"Session {session_id} not found or expired"
        )
    
    return {
        "session_id": session_id,
        "player_name": state.player_name,
        "character_class": state.character_class,
        "current_scene": state.current_scene,
        "available_actions": state.available_actions,
        "player_stats": {
            "hp": state.character_stats.health_points,
            "max_hp": state.character_stats.max_health_points,
            "mana": state.character_stats.mana_points,
            "max_mana": state.character_stats.max_mana_points,
            "stamina": state.character_stats.stamina_points,
            "max_stamina": state.character_stats.max_stamina_points,
            "level": state.character_stats.level,
            "xp": state.character_stats.experience_points,
            "xp_to_next": state.character_stats.experience_to_next_level,
            "inventory": state.inventory
        },
        "quest_info": {
            "main_quest": state.main_quest,
            "side_quests": state.side_quests
        },
        "game_over": state.character_stats.health_points <= 0
    }


@app.get("/game/{session_id}/character")
def get_character_sheet(session_id: str):
    """View detailed character sheet with attributes"""
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=404, 
            detail=f"Session {session_id} not found or expired"
        )
    
    modifiers = state.attributes.get_all_modifiers()
    
    return {
        "session_id": session_id,
        "player_name": state.player_name,
        "character_class": state.character_class,
        "level": state.character_stats.level,
        "experience": {
            "current": state.character_stats.experience_points,
            "to_next_level": state.character_stats.experience_to_next_level,
            "percentage": round(
                (state.character_stats.experience_points / state.character_stats.experience_to_next_level) * 100, 
                1
            )
        },
        "attributes": {
            "strength": {
                "value": state.attributes.strength,
                "modifier": modifiers["strength"]
            },
            "dexterity": {
                "value": state.attributes.dexterity,
                "modifier": modifiers["dexterity"]
            },
            "constitution": {
                "value": state.attributes.constitution,
                "modifier": modifiers["constitution"]
            },
            "intelligence": {
                "value": state.attributes.intelligence,
                "modifier": modifiers["intelligence"]
            },
            "wisdom": {
                "value": state.attributes.wisdom,
                "modifier": modifiers["wisdom"]
            },
            "charisma": {
                "value": state.attributes.charisma,
                "modifier": modifiers["charisma"]
            }
        },
        "resources": {
            "health": {
                "current": state.character_stats.health_points,
                "max": state.character_stats.max_health_points,
                "percentage": round(state.character_stats.get_health_percentage() * 100, 1)
            },
            "mana": {
                "current": state.character_stats.mana_points,
                "max": state.character_stats.max_mana_points,
                "percentage": round(state.character_stats.get_mana_percentage() * 100, 1)
            },
            "stamina": {
                "current": state.character_stats.stamina_points,
                "max": state.character_stats.max_stamina_points,
                "percentage": round(state.character_stats.get_stamina_percentage() * 100, 1)
            }
        },
        "available_points": {
            "attribute_points": state.character_stats.available_attribute_points,
            "skill_points": state.character_stats.available_skill_points
        },
        "inventory": state.inventory,
        "summary": state.get_character_summary()
    }


@app.post("/game/{session_id}/attribute")
def spend_attribute_point(session_id: str, request: AttributeSpendRequest):
    """Spend an attribute point to increase an attribute"""
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=404, 
            detail=f"Session {session_id} not found or expired"
        )
    
    # Try to spend the point
    success = state.spend_attribute_point(request.attribute)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot increase {request.attribute.value}. Either no points available or attribute is at max (20)."
        )
    
    # Update session
    session_manager.update_session(session_id, state)
    
    api_logger.info(
        f"Attribute point spent in session {session_id}",
        extra={
            "session_id": session_id,
            "attribute": request.attribute.value,
            "new_value": getattr(state.attributes, request.attribute.value),
            "remaining_points": state.character_stats.available_attribute_points,
            "event": "attribute_increased"
        }
    )
    
    modifiers = state.attributes.get_all_modifiers()
    
    return {
        "success": True,
        "attribute": request.attribute.value,
        "new_value": getattr(state.attributes, request.attribute.value),
        "new_modifier": modifiers[request.attribute.value],
        "remaining_attribute_points": state.character_stats.available_attribute_points,
        "updated_stats": {
            "max_hp": state.character_stats.max_health_points,
            "max_mana": state.character_stats.max_mana_points,
            "max_stamina": state.character_stats.max_stamina_points
        }
    }


@app.delete("/game/{session_id}")
def end_game(session_id: str):
    """End your game session"""
    if session_manager.delete_session(session_id):
        return {
            "message": "Game session ended",
            "session_id": session_id
        }
    raise HTTPException(
        status_code=404, 
        detail=f"Session {session_id} not found"
    )


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "active_sessions": session_manager.get_session_count()
    }


# uvicorn main:app --reload 

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional

class StartCombatRequest(BaseModel):
    """Request to start a combat encounter"""
    enemy_type: Optional[str] = Field(None, description="Specific enemy type or 'random' or 'boss'")
    enemy_level: Optional[int] = Field(1, ge=1, le=20, description="Enemy level")
    enemy_count: Optional[int] = Field(1, ge=1, le=5, description="Number of enemies")

class CombatActionRequest(BaseModel):
    """Request to perform a combat action"""
    action_type: str = Field(..., description="attack, ability, defend, item, flee")
    target_index: Optional[int] = Field(0, description="Index of enemy target")
    ability_name: Optional[str] = Field(None, description="Name of ability to use")
    item_name: Optional[str] = Field(None, description="Name of item to use")



# ==================== PASTE THESE INTO main.py ====================


@app.post("/game/{session_id}/combat/start")
def start_combat(session_id: str, request: StartCombatRequest):
    '''
    Start a combat encounter.
    
    Creates enemies and initiates turn-based combat.
    '''
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    if state.in_combat:
        raise HTTPException(status_code=400, detail="Already in combat")
    
    # Create combat system for this session
    if session_id not in combat_systems:
        combat_systems[session_id] = CombatSystem()
    
    combat_system = combat_systems[session_id]
    
    # Create enemies
    enemies = []
    
    if request.enemy_type == "boss":
        enemies.append(create_dragon_boss(level=request.enemy_level))
    elif request.enemy_type == "random":
        for _ in range(request.enemy_count):
            enemies.append(spawn_random_enemy(difficulty=request.enemy_level))
    else:
        # Specific enemy type
        enemy_creators = {
            "goblin": create_goblin,
            "orc": create_orc,
            "necromancer": create_necromancer,
        }
        
        creator = enemy_creators.get(request.enemy_type)
        if creator:
            for _ in range(request.enemy_count):
                enemies.append(creator(level=request.enemy_level))
        else:
            # Use spawn_random_enemy which takes 'difficulty' not 'level'
            for _ in range(request.enemy_count):
                enemies.append(spawn_random_enemy(difficulty=request.enemy_level))
    
    # Start combat
    result = combat_system.start_combat(state, enemies)
    
    state.in_combat = True
    session_manager.update_session(session_id, state)
    
    api_logger.info(
        f"Combat started in session {session_id}",
        extra={
            "session_id": session_id,
            "enemy_count": len(enemies),
            "event": "combat_initiated"
        }
    )
    
    return {
        "session_id": session_id,
        **result,
        "available_actions": [
            "Attack",
            "Use Ability",
            "Defend",
            "Use Item",
            "Flee"
        ]
    }


@app.post("/game/{session_id}/combat/action")
def perform_combat_action(session_id: str, request: CombatActionRequest):
    '''
    Perform an action in combat.
    
    Executes player action, then enemy turns, updates status effects.
    '''
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    if not state.in_combat:
        raise HTTPException(status_code=400, detail="Not in combat")
    
    if session_id not in combat_systems:
        raise HTTPException(status_code=500, detail="Combat system not initialized")
    
    combat_system = combat_systems[session_id]
    
    # Perform action based on type
    try:
        if request.action_type == "attack":
            result = combat_system.player_attack(state, request.target_index)
        
        elif request.action_type == "ability":
            if not request.ability_name:
                raise HTTPException(status_code=400, detail="ability_name required")
            result = combat_system.player_use_ability(
                state, 
                request.ability_name, 
                request.target_index
            )
        
        elif request.action_type == "defend":
            result = combat_system.player_defend(state)
        
        elif request.action_type == "item":
            if not request.item_name:
                raise HTTPException(status_code=400, detail="item_name required")
            result = combat_system.player_use_item(state, request.item_name)
        
        elif request.action_type == "flee":
            result = combat_system.player_flee(state)
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {request.action_type}")
        
        # Update session
        if result.get("combat_ended"):
            state.in_combat = False
            if session_id in combat_systems:
                del combat_systems[session_id]
        
        session_manager.update_session(session_id, state)
        
        return {
            "session_id": session_id,
            **result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/game/{session_id}/combat/status")
def get_combat_status(session_id: str):
    '''Get current combat status'''
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    if not state.in_combat:
        return {
            "in_combat": False,
            "message": "Not currently in combat"
        }
    
    if session_id not in combat_systems:
        raise HTTPException(status_code=500, detail="Combat system not initialized")
    
    combat_system = combat_systems[session_id]
    
    return {
        "in_combat": True,
        "enemies": [combat_system._enemy_to_dict(e) for e in combat_system.enemies if e.is_alive],
        "player_stats": combat_system._player_stats_dict(state),
        "combat_log": combat_system.combat_log.get_last_n_events(20),
        "turn_order": combat_system.turn_order,
        "available_abilities": [
            {"name": "Power Strike", "stamina_cost": 15, "damage": "High"},
            {"name": "Fireball", "mana_cost": 20, "damage": "Very High", "element": "fire"},
            {"name": "Heal", "mana_cost": 25, "effect": "Restore HP"}
        ]
    }


@app.post("/game/{session_id}/combat/end")
def force_end_combat(session_id: str):
    '''Force end combat (debug/admin endpoint)'''
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    if session_id in combat_systems:
        combat_systems[session_id].end_combat(state)
        del combat_systems[session_id]
    
    state.in_combat = False
    session_manager.update_session(session_id, state)
    
    return {
        "message": "Combat ended",
        "session_id": session_id
    }