from models.game_state import GameState
from utils.logger import get_logger, log_performance, log_game_event
from dotenv import load_dotenv

load_dotenv()

# Initialize logger
main_logger = get_logger("game_engine")

@log_performance(main_logger)
def start_session(input_state: GameState) -> GameState:
    """Initialize a new game session"""
    
    main_logger.info(
        "Starting new game session",
        extra={
            "player_name": input_state.player_name,
            "character_class": input_state.character_class,
            "setting": input_state.setting,
            "event": "session_start"
        }
    )
    
    log_game_event(
        "session_started",
        player_name=input_state.player_name,
        character_class=input_state.character_class,
        setting=input_state.setting
    )
    
    updated_state = input_state.model_copy(update={"game_started": True})
    
    main_logger.debug(
        "Game session initialized successfully",
        extra={
            "game_started": True,
            "player_hp": updated_state.character_stats.health_points,
            "event": "session_initialized"
        }
    )
    
    return updated_state