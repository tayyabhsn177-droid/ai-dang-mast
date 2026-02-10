from models.game_state import GameState, AttributeType
from langchain_core.prompts import PromptTemplate
from utils.logger import get_logger, log_performance, log_game_event
from dotenv import load_dotenv
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

model = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai", temperature=0.7)


@log_performance(main_logger)
def action_resolution(input_state: GameState) -> GameState:
    """Resolve player action with dice roll, attribute modifiers, and consequences"""
    
    main_logger.info(
        "Resolving player action",
        extra={
            "action": input_state.selected_action,
            "player_hp": input_state.character_stats.health_points,
            "event": "action_resolution_start"
        }
    )
    
    try:
        # Make a deep copy to avoid modifying original state
        updated_state = input_state.model_copy(deep=True)
        
        # Determine which attribute applies to this action
        action_lower = input_state.selected_action.lower()
        
        # Action type detection
        attribute_modifier = 0
        attribute_used = None
        
        if any(word in action_lower for word in ["fight", "attack", "strike", "punch", "slash"]):
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.STRENGTH)
            attribute_used = "STRENGTH"
        elif any(word in action_lower for word in ["dodge", "sneak", "hide", "shoot", "aim"]):
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.DEXTERITY)
            attribute_used = "DEXTERITY"
        elif any(word in action_lower for word in ["cast", "spell", "magic", "arcane", "investigate"]):
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.INTELLIGENCE)
            attribute_used = "INTELLIGENCE"
        elif any(word in action_lower for word in ["perceive", "sense", "notice", "insight"]):
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.WISDOM)
            attribute_used = "WISDOM"
        elif any(word in action_lower for word in ["persuade", "charm", "intimidate", "negotiate"]):
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.CHARISMA)
            attribute_used = "CHARISMA"
        else:
            # Default to dexterity for general actions
            attribute_modifier = updated_state.attributes.get_modifier(AttributeType.DEXTERITY)
            attribute_used = "DEXTERITY"
        
        # Check if this is a rest action
        if "rest" in action_lower:
            rest_type = "long" if "long" in action_lower or "camp" in action_lower else "short"
            recovered = updated_state.rest(rest_type)
            
            main_logger.info(
                f"Player took {rest_type} rest",
                extra={
                    "rest_type": rest_type,
                    "health_recovered": recovered["health"],
                    "mana_recovered": recovered["mana"],
                    "stamina_recovered": recovered["stamina"],
                    "event": "rest_taken"
                }
            )
            
            # Generate rest narration
            rest_narration = f"""You take a {rest_type} rest to recover your strength.

As you rest, you feel your energy returning:
- Health recovered: {recovered['health']} HP
- Mana recovered: {recovered['mana']} MP
- Stamina recovered: {recovered['stamina']} SP

You are now at {updated_state.character_stats.health_points}/{updated_state.character_stats.max_health_points} HP, feeling refreshed and ready to continue.

Next Possible Actions:
1. Continue your journey
2. Check your surroundings carefully
3. Review your inventory
4. Explore the area"""
            
            updated_state.action_result = rest_narration
            updated_state.current_scene = rest_narration
            updated_state.available_actions = [
                "Continue your journey",
                "Check your surroundings carefully", 
                "Review your inventory",
                "Explore the area"
            ]
            updated_state.selected_action = ""
            updated_state.last_dice_roll = 0
            updated_state.last_roll_outcome = "rest"
            
            log_game_event(
                "rest_completed",
                rest_type=rest_type,
                recovered=recovered
            )
            
            return updated_state
        
        # Roll dice with attribute modifier
        base_roll = roll_dice()
        modified_roll = base_roll + attribute_modifier
        
        # Determine success (DC 10 for normal actions)
        roll_outcome = "success" if modified_roll >= 10 else "failure"
        
        main_logger.info(
            "Dice rolled for action resolution",
            extra={
                "base_roll": base_roll,
                "attribute_modifier": attribute_modifier,
                "attribute_used": attribute_used,
                "modified_roll": modified_roll,
                "outcome": roll_outcome,
                "success_threshold": 10,
                "event": "dice_rolled"
            }
        )

        SYSTEM_PROMPT = """You are a fantasy game master AI guiding a player through an adventure.

When narrating action outcomes:
- The player rolled {base_roll} (d20) + {attribute_modifier} ({attribute_used}) = {modified_roll}
- Success threshold is 10
- If the player fails a dice roll during a dangerous or combat-related action, describe an enemy hitting the player.
- Use clear phrases like "The enemy attacks you!" or "You are hit!" to show when the player takes damage.
- If the player succeeds, describe their success vividly, including how they overcame danger, won a fight, or found something valuable.
- If the player wins an encounter or solves a challenge (especially on high rolls 15+), they may find loot. Mention this creatively.
- If the player fails an action, narrate how they are hurt (describe wounds, strikes, traps, curses, or falls).
- Always assume damage taken on failure is between 5 to 15 HP (don't invent different damage numbers yourself).
- Keep the narration immersive but concise (2-3 paragraphs max).

Inputs you will receive:
- Current Scene: {current_scene}
- Selected Action: {selected_action}
- Base Dice Roll: {base_roll}
- Attribute Modifier: {attribute_modifier} ({attribute_used})
- Modified Roll: {modified_roll}
- Roll Outcome: {roll_outcome}

At the end of the narration, always clearly list exactly 4 next possible actions as simple numbered choices:

Example Format:

Next Possible Actions:
1. [Short Action 1]
2. [Short Action 2]
3. [Short Action 3]
4. [Short Action 4]

Important Guidelines:
- Actions must be actionable (verbs like Explore, Fight, Talk, Investigate, Rest).
- Avoid vague options like "Think about it" or "Wait".
- Actions must fit the current scene context.
- Keep action choices short and exciting (no longer than 6 words each).
- Include at least one "Rest" option if the player is injured.
"""

        prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
        formatted_prompt = prompt.format(
            current_scene=input_state.current_scene,
            selected_action=input_state.selected_action,
            base_roll=base_roll,
            attribute_modifier=f"{attribute_modifier:+d}",
            attribute_used=attribute_used,
            modified_roll=modified_roll,
            roll_outcome=roll_outcome
        )
        
        ai_logger.debug(
            "Prepared action resolution prompt",
            extra={
                "prompt_length": len(formatted_prompt),
                "dice_roll": modified_roll,
                "outcome": roll_outcome,
                "attribute_used": attribute_used
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
        new_actions = [m.strip() for m in matches][:4]  # Take only first 4
        
        if not new_actions or len(new_actions) < 4:
            main_logger.warning("Incomplete actions found in resolution, using defaults")
            new_actions = [
                "Continue exploring",
                "Rest and recover",
                "Check inventory",
                "Look around carefully"
            ]

        # Handle consequences
        loot_gained = None
        damage_info = None
        xp_gained = 0

        # Success - Grant XP and potentially loot
        if roll_outcome == "success":
            # Base XP for success
            xp_gained = 50
            
            # High roll (15+) - extra XP and loot
            if modified_roll >= 15:
                xp_gained = 100
                loot_options = [
                    "Healing Potion", 
                    "Silver Sword", 
                    "Ancient Scroll", 
                    "Mystic Ring", 
                    "Gold Coins (50)",
                    "Mana Crystal",
                    "Elixir of Strength"
                ]
                loot = random.choice(loot_options)
                updated_state.inventory = add_item_to_inventory(updated_state.inventory, loot)
                loot_gained = loot
                
                main_logger.info(
                    "Player succeeded with high roll - loot and bonus XP granted",
                    extra={
                        "loot": loot,
                        "xp_gained": xp_gained,
                        "modified_roll": modified_roll,
                        "event": "high_success"
                    }
                )
            else:
                main_logger.info(
                    "Player succeeded - XP granted",
                    extra={
                        "xp_gained": xp_gained,
                        "modified_roll": modified_roll,
                        "event": "success"
                    }
                )
        
        # Failure - Take damage and small XP
        else:
            damage = random.randint(5, 15)
            damage_info = updated_state.take_damage(damage)
            xp_gained = 10  # Small XP for trying
            
            main_logger.warning(
                "Player failed action - damage taken",
                extra={
                    "damage_dealt": damage_info["damage_dealt"],
                    "damage_reduced": damage_info["damage_reduced"],
                    "hp_after": damage_info["remaining_hp"],
                    "modified_roll": modified_roll,
                    "event": "failure"
                }
            )
        
        # Award experience
        leveled_up = updated_state.add_experience(xp_gained)
        
        if leveled_up:
            main_logger.info(
                "Player leveled up!",
                extra={
                    "new_level": updated_state.character_stats.level,
                    "attribute_points_gained": 2,
                    "skill_points_gained": 5,
                    "event": "level_up"
                }
            )

        # Update state
        updated_state.action_result = result
        updated_state.current_scene = result
        updated_state.available_actions = new_actions
        updated_state.selected_action = ""
        updated_state.last_dice_roll = modified_roll
        updated_state.last_roll_outcome = roll_outcome
        
        # Log the complete action resolution
        log_game_event(
            "action_resolved",
            action=input_state.selected_action,
            base_roll=base_roll,
            attribute_modifier=attribute_modifier,
            attribute_used=attribute_used,
            modified_roll=modified_roll,
            outcome=roll_outcome,
            damage_taken=damage_info["damage_dealt"] if damage_info else 0,
            loot_gained=loot_gained,
            xp_gained=xp_gained,
            leveled_up=leveled_up,
            hp_after=updated_state.character_stats.health_points,
            new_actions_count=len(new_actions)
        )
        
        main_logger.info(
            "Action resolution completed successfully",
            extra={
                "outcome": roll_outcome,
                "xp_gained": xp_gained,
                "leveled_up": leveled_up,
                "hp": updated_state.character_stats.health_points,
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