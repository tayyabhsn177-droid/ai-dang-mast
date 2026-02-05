from utils.game_state import GameState
from langchain_core.prompts import PromptTemplate
from utils.logger import (
    get_logger, 
    log_performance, 
    log_game_event, 
)

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chat_models import init_chat_model
import re
import random
import time
from utils.inventory_manager import add_item_to_inventory
from utils.dice_roller import roll_dice

load_dotenv()

# Initialize loggers
main_logger = get_logger("game_engine")
ai_logger = get_logger("ai")

model = init_chat_model("gemini-2.5-flash_lite", model_provider="google_genai", temperature=0.7)


# Action Resolution Node
@log_performance(main_logger)
def action_resolution(input_state: GameState) -> GameState:
    """Resolve player action with dice roll and consequences"""
    
    main_logger.info(
        "Resolving player action",
        extra={
            "action": input_state.selected_action,
            "player_hp": input_state.health_points,
            "event": "action_resolution_start"
        }
    )
    
    try:
        # Roll dice
        dice_result = roll_dice()
        roll_outcome = "success" if dice_result >= 10 else "failure"
        
        main_logger.info(
            "Dice rolled for action resolution",
            extra={
                "dice_roll": dice_result,
                "outcome": roll_outcome,
                "success_threshold": 10,
                "event": "dice_rolled"
            }
        )

        SYSTEM_PROMPT = """You are a fantasy game master AI guiding a player through an adventure.

When narrating action outcomes:
- If the player fails a dice roll during a dangerous or combat-related action, describe an enemy hitting the player.
- Use clear phrases like "The enemy attacks you!" or "You are hit!" to show when the player takes damage.
- If the player succeeds, describe their success vividly, including how they overcame danger, won a fight, or found something valuable.
- If the player wins an encounter or solves a challenge, they may find loot. Mention this creatively.
- If the player fails an action, narrate how they are hurt (describe wounds, strikes, traps, curses, or falls).
- Always assume damage taken on failure is between 5 to 15 HP (don't invent different damage numbers yourself).
- Keep the narration immersive but concise.

Inputs you will receive:
- Current Scene: {current_scene}
- Selected Action: {selected_action}
- Dice Roll: {dice_roll}
- Roll Outcome: {roll_outcome}

At the end of the narration, always clearly list exactly 4 next possible actions as simple numbered choices:

Example Format:

Next Possible Actions:
1. [Short Action 1]
2. [Short Action 2]
3. [Short Action 3]
4. [Short Action 4]

Important Guidelines:
- Actions must be actionable (verbs like Explore, Fight, Talk, Investigate).
- Avoid vague options like "Think about it" or "Wait".
- Actions must fit the current scene context.
- Keep action choices short and exciting (no longer than 6 words each).
"""

        prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
        formatted_prompt = prompt.format(
            current_scene=input_state.current_scene,
            selected_action=input_state.selected_action,
            dice_roll=dice_result,
            roll_outcome=roll_outcome
        )
        
        ai_logger.debug(
            "Prepared action resolution prompt",
            extra={
                "prompt_length": len(formatted_prompt),
                "dice_roll": dice_result,
                "outcome": roll_outcome
            }
        )

        # Call AI model for resolution
        start_time = time.time()
        result = model.invoke(formatted_prompt).content
        ai_response_time = (time.time() - start_time) * 1000
        
        ai_logger.info(
            "Generated action resolution",
            extra={
                "resolution_length": len(result),
                "ai_response_time_ms": round(ai_response_time, 2),
                "event": "action_resolution_generated"
            }
        )

        # Extract new actions
        matches = re.findall(r'\d+\.\s(.+)', result)
        new_actions = [m.strip() for m in matches]
        
        if not new_actions:
            main_logger.warning("No new actions found in resolution, using defaults")
            new_actions = [
                "Continue exploring",
                "Check inventory",
                "Rest and recover",
                "Look around carefully"
            ]

        # Handle consequences
        updated_inventory = input_state.inventory.copy()
        updated_hp = input_state.health_points
        loot_gained = None
        damage_taken = 0

        if roll_outcome == "success" and dice_result >= 15:
            # High success - grant loot
            loot_options = ["Healing Potion", "Silver Sword", "Ancient Scroll", "Mystic Ring", "Gold Coins"]
            loot = random.choice(loot_options)
            updated_inventory = add_item_to_inventory(updated_inventory, loot)
            loot_gained = loot
            
            main_logger.info(
                "Player succeeded with high roll - loot granted",
                extra={
                    "loot": loot,
                    "dice_roll": dice_result,
                    "event": "loot_granted"
                }
            )

        elif roll_outcome == "failure":
            # Failure - take damage
            damage = random.randint(5, 15)
            updated_hp = max(0, updated_hp - damage)
            damage_taken = damage
            
            main_logger.warning(
                "Player failed action - damage taken",
                extra={
                    "damage": damage,
                    "hp_before": input_state.health_points,
                    "hp_after": updated_hp,
                    "dice_roll": dice_result,
                    "event": "damage_taken"
                }
            )

        updated_state = input_state.copy(update={
            "action_result": result,
            "new_available_actions": new_actions,
            "last_dice_roll": dice_result,
            "last_roll_outcome": roll_outcome,
            "inventory": updated_inventory,
            "health_points": updated_hp
        })
        
        # Log the complete action resolution
        log_game_event(
            "action_resolved",
            action=input_state.selected_action,
            dice_roll=dice_result,
            outcome=roll_outcome,
            damage_taken=damage_taken,
            loot_gained=loot_gained,
            hp_after=updated_hp,
            new_actions_count=len(new_actions)
        )
        
        main_logger.info(
            "Action resolution completed successfully",
            extra={
                "outcome": roll_outcome,
                "hp_change": updated_hp - input_state.health_points,
                "inventory_change": len(updated_inventory) - len(input_state.inventory),
                "event": "action_resolution_complete"
            }
        )
        
        return updated_state
        
    except Exception as e:
        main_logger.error(
            "Failed to resolve player action",
            exc_info=True,
            extra={
                "action": input_state.selected_action,
                "error_type": type(e).__name__,
                "event": "action_resolution_failed"
            }
        )
        raise