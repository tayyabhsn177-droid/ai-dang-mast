from models.game_state import GameState
from langchain_core.prompts import PromptTemplate
from utils.logger import get_logger, log_performance, log_game_event
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import time

load_dotenv()

# Initialize logger
ai_logger = get_logger("ai")

model = init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0.7)

@log_performance(ai_logger)
def world_and_quest(input_state: GameState) -> GameState:
    """Generate world introduction and main quest"""
    
    ai_logger.info(
        "Generating world and quest content",
        extra={
            "player_name": input_state.player_name,
            "character_class": input_state.character_class,
            "setting": input_state.setting,
            "event": "world_generation_start"
        }
    )
    
    try:
        SYSTEM_PROMPT = """You are an expert fantasy storyteller AI. A new player has joined your world.

Based on the following player details, generate a captivating intro:
- Player Name: {player_name}
- Class: {character_class}
- Setting: {setting}
- Preferences: {preferences}

Respond with exactly 4 sections:
1. 🌍 World Introduction (2-3 sentences about the world setting)
2. 🏰 Starting Location Description (2-3 sentences describing where the player begins)
3. 👤 Key NPCs (1-2 NPCs with name and brief personality)
4. 🎯 Main Quest Hook (1-2 sentences introducing the main conflict or goal)

Keep each section concise and engaging."""
        
        prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
        formatted_prompt = prompt.format(
            player_name=input_state.player_name,
            character_class=input_state.character_class,
            setting=input_state.setting,
            preferences=input_state.preferences
        )
        
        ai_logger.debug(
            "Formatted prompt for AI model",
            extra={
                "formatted_prompt_length": len(formatted_prompt),
                "model": "gemini-2.5-flash"
            }
        )
        
        # Call AI model
        start_time = time.time()
        result = model.invoke(formatted_prompt).content
        ai_response_time = (time.time() - start_time) * 1000
        
        ai_logger.info(
            "Received AI response for world generation",
            extra={
                "response_length": len(result),
                "ai_response_time_ms": round(ai_response_time, 2),
                "event": "ai_response_received"
            }
        )
        
        # Parse response
        sections = result.split("\n")
        filtered_sections = [section.strip() for section in sections if section.strip()]
        
        if len(filtered_sections) < 4:
            ai_logger.warning(
                "AI response has fewer sections than expected",
                extra={
                    "expected_sections": 4,
                    "actual_sections": len(filtered_sections),
                    "sections": filtered_sections
                }
            )
        
        updated_state = input_state.model_copy(update={
            "world_intro": filtered_sections[0] if len(filtered_sections) > 0 else "A mysterious world awaits...",
            "location_intro": filtered_sections[1] if len(filtered_sections) > 1 else "You find yourself in an unknown place.",
            "npcs": [filtered_sections[2]] if len(filtered_sections) > 2 else ["A mysterious stranger"],
            "main_quest": filtered_sections[3] if len(filtered_sections) > 3 else "Your quest begins..."
        })
        
        log_game_event(
            "world_generated",
            world_intro_length=len(updated_state.world_intro),
            location_intro_length=len(updated_state.location_intro),
            npcs_count=len(updated_state.npcs),
            main_quest_length=len(updated_state.main_quest)
        )
        
        ai_logger.info(
            "World and quest generation completed successfully",
            extra={
                "world_sections_generated": len(filtered_sections),
                "event": "world_generation_complete"
            }
        )
        
        return updated_state
        
    except Exception as e:
        ai_logger.error(
            "Failed to generate world and quest content",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "event": "world_generation_failed"
            }
        )
        raise