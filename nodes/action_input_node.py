from utils.game_state import GameState
from utils.logger import (
    get_logger, 
    log_performance, 
    log_game_event, 
)

from dotenv import load_dotenv
load_dotenv()

# Initialize loggers
main_logger = get_logger("game_engine")

# Action Selection Node (UI will handle choosing)
@log_performance(main_logger)
def action_input(input_state: GameState) -> GameState:
    """Process player action selection"""
    
    main_logger.info(
        "Processing action input",
        extra={
            "selected_action": input_state.selected_action,
            "available_actions_count": len(input_state.available_actions),
            "event": "action_input_processed"
        }
    )
    
    if input_state.selected_action:
        log_game_event(
            "action_selected",
            action=input_state.selected_action,
            player_name=input_state.player_name
        )
    
    return input_state