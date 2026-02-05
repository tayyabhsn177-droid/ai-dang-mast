from models.game_state import GameState
from langchain_core.prompts import PromptTemplate
from utils.logger import get_logger, log_performance, log_game_event
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import re
import time

load_dotenv()

# Initialize logger
ai_logger = get_logger("ai")

model = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai", temperature=0.7)

@log_performance(ai_logger)
def narration(input_state: GameState) -> GameState:
    """Generate scene narration and available actions"""
    
    ai_logger.info(
        "Generating scene narration",
        extra={
            "has_action_result": bool(input_state.action_result),
            "current_location": input_state.location_intro[:50] + "..." if input_state.location_intro else "",
            "event": "narration_start"
        }
    )
    
    try:
        SYSTEM_PROMPT = """You are a master narrator for a tabletop role-playing game.

Based on the following game data, narrate the current scene for the player:
- 🌍 World Introduction: {world_intro}
- 🏰 Location Description: {location_intro}
- 👤 NPCs Present: {npcs}
- 🎯 Main Quest: {main_quest}

Create a vivid, immersive description of:
- What the player sees, hears, and senses
- What the NPCs are doing
- Any important visual or emotional cues

End your narration by offering exactly 4 possible actions the player can take.
List them as:

Next Possible Actions:
1. [Action 1]
2. [Action 2]
3. [Action 3]
4. [Action 4]

Example actions: Talk to [NPC], Explore [area], Investigate [object], Rest and recover, Move to [place]

**DO NOT make any decisions for the player.**
Just narrate and offer choices."""

        prompt = PromptTemplate.from_template(SYSTEM_PROMPT)

        # Use action result if available, otherwise use location intro
        location_intro = input_state.action_result if input_state.action_result else input_state.location_intro

        formatted_prompt = prompt.format(
            world_intro=input_state.world_intro,
            location_intro=location_intro,
            npcs=input_state.npcs,
            main_quest=input_state.main_quest
        )
        
        ai_logger.debug(
            "Prepared narration prompt",
            extra={
                "prompt_length": len(formatted_prompt),
                "npcs_count": len(input_state.npcs)
            }
        )

        # Call AI model
        start_time = time.time()
        result = model.invoke(formatted_prompt).content
        ai_response_time = (time.time() - start_time) * 1000
        
        ai_logger.info(
            "Generated scene narration",
            extra={
                "narration_length": len(result),
                "ai_response_time_ms": round(ai_response_time, 2),
                "event": "narration_generated"
            }
        )

        # Extract actions from narration
        matches = re.findall(r'\d+\.\s(.+)', result)
        actions = [m.strip() for m in matches][:4]  # Take only first 4
        
        if not actions or len(actions) < 4:
            ai_logger.warning(
                "Incomplete actions in narration, using fallback",
                extra={"actions_found": len(actions)}
            )
            actions = [
                "Explore further into the ruins",
                "Talk to nearby NPCs",
                "Search for hidden items",
                "Rest and recover"
            ]

        updated_state = input_state.model_copy(update={
            "current_scene": result,
            "available_actions": actions
        })
        
        log_game_event(
            "scene_narrated",
            scene_length=len(result),
            actions_available=len(actions)
        )
        
        return updated_state

    except Exception as e:
        ai_logger.error(
            "Failed to generate narration",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "event": "narration_failed"
            }
        )
        raise