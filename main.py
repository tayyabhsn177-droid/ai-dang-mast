# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.game_state import GameState

from graph_builder import build_graph
from fastapi.responses import JSONResponse

app = FastAPI(title="AI Dungeon Master", version="1.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph , action_only_graph, next_turn_graph = build_graph()

# Initialize the global state variable
global updated_state
updated_state = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Dungeon Master API!"}

@app.get("/status")
def get_status():
    if not updated_state:
        return JSONResponse(content={"message": "No game session started yet."}, status_code=404)
    return updated_state.dict()


@app.post("/start-session")
def start_session(state: GameState) -> GameState:
    updated_state = graph.invoke(state)
    return updated_state

@app.post("/choose-action")
def choose_action(game_state: GameState):
    updated_state = action_only_graph.invoke(game_state)
    return updated_state

@app.post("/next-turn")
def next_turn(game_state: GameState):
    global updated_state
    if not updated_state:
        return {"message": "Game not started. Use /start-session to begin the game."}
    
    # Example: If player's health is 0, game ends
    if updated_state.health_points <= 0:
        return {"message": "Game Over! You have no health remaining."}

    # Check if the game has reached the end (e.g., quest completion)
    if updated_state.main_quest == "completed":
        return {"message": "Congratulations! You have completed your quest."}
    
    updated_state = next_turn_graph.invoke(game_state, start_at="narration")
    return updated_state

@app.post("/show-inventory")
def show_inventory(game_state: GameState):
    return {
        "inventory": game_state.inventory,
        "player_hp": game_state.player_hp,
        "max_hp": game_state.max_hp,
        "experience_points": game_state.experience_points,
        "level": game_state.level
    }

    # uvicorn main:app --reload