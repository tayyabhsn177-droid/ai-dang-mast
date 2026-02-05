from langgraph.graph import StateGraph, END
from utils.game_state import GameState
from utils.logger import get_logger

# Initialize logger
main_logger = get_logger("game_engine")

from nodes.start_session_node import start_session
from nodes.world_and_quest_node import world_and_quest
from nodes.narration_node import narration
from nodes.action_input_node import action_input
from nodes.action_resolution_node import action_resolution

def build_graph():
    """Build and return the game workflow graphs"""
    
    main_logger.info(
        "Building game workflow graphs",
        extra={"event": "graph_building_start"}
    )

    try:
        # Initialize main graph
        builder = StateGraph(GameState)

        # Add nodes
        builder.add_node("start_session", start_session)
        builder.add_node("world_and_quest", world_and_quest)
        builder.add_node("narration", narration)
        builder.add_node("action_input", action_input)
        builder.add_node("action_resolution", action_resolution)

        # Setup edges (flow connections)
        builder.add_edge("start_session", "world_and_quest")
        builder.add_edge("world_and_quest", "narration")
        builder.add_edge("narration", "action_input")  
        builder.add_edge("action_input", "action_resolution")  

        builder.set_entry_point("start_session")
        builder.set_finish_point("action_resolution")

        # Compile the main graph
        graph = builder.compile()
        
        main_logger.debug(
            "Main game graph compiled successfully",
            extra={
                "nodes": ["start_session", "world_and_quest", "narration", "action_input", "action_resolution"],
                "event": "main_graph_compiled"
            }
        )

        # Build mini graph for action resolution only
        mini_builder = StateGraph(GameState)
        mini_builder.add_node("action_resolution", action_resolution)
        mini_builder.add_edge("action_resolution", END)
        mini_builder.set_entry_point("action_resolution")
        action_only_graph = mini_builder.compile()
        
        main_logger.debug(
            "Action-only graph compiled successfully",
            extra={
                "nodes": ["action_resolution"],
                "event": "action_graph_compiled"
            }
        )

        # Build graph for continuing turns
        next_turn_graph = StateGraph(GameState)
        next_turn_graph.add_node("narration", narration)
        next_turn_graph.add_node("action_input", action_input)
        next_turn_graph.add_node("action_resolution", action_resolution)

        next_turn_graph.add_edge("narration", "action_input")
        next_turn_graph.add_edge("action_input", "action_resolution")

        next_turn_graph.set_entry_point("narration")
        next_turn_graph.set_finish_point("action_resolution")
        
        main_logger.debug(
            "Next-turn graph compiled successfully",
            extra={
                "nodes": ["narration", "action_input", "action_resolution"],
                "event": "next_turn_graph_compiled"
            }
        )

        main_logger.info(
            "All game workflow graphs built successfully",
            extra={
                "graphs_built": ["main", "action_only", "next_turn"],
                "event": "graph_building_complete"
            }
        )

        return graph, action_only_graph, next_turn_graph
        
    except Exception as e:
        main_logger.error(
            "Failed to build game workflow graphs",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "event": "graph_building_failed"
            }
        )
        raise