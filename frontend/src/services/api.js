import axios from 'axios';

// Base API URL - change this to match your backend
const API_BASE_URL = 'http://localhost:8000';



// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Game API endpoints
export const gameApi = {
  // Start a new game
  startGame: async (playerName, characterClass, setting) => {
    try {
      const response = await apiClient.post('/game/start', {
        player_name: playerName,
        character_class: characterClass,
        setting: setting,
      });
      return response.data;
    } catch (error) {
      console.error('Error starting game:', error);
      throw error;
    }
  },

  // Take an action
  takeAction: async (sessionId, action) => {
    try {
      const response = await apiClient.post(`/game/${sessionId}/action`, {
        action: action,
      });
      return response.data;
    } catch (error) {
      console.error('Error taking action:', error);
      throw error;
    }
  },

  // Get game state
  getGameState: async (sessionId) => {
    try {
      const response = await apiClient.get(`/game/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting game state:', error);
      throw error;
    }
  },

  // Get character sheet
  getCharacterSheet: async (sessionId) => {
    try {
      const response = await apiClient.get(`/game/${sessionId}/character`);
      return response.data;
    } catch (error) {
      console.error('Error getting character sheet:', error);
      throw error;
    }
  },

  // Spend attribute point
  spendAttributePoint: async (sessionId, attribute) => {
    try {
      const response = await apiClient.post(`/game/${sessionId}/attribute`, {
        attribute: attribute,
      });
      return response.data;
    } catch (error) {
      console.error('Error spending attribute point:', error);
      throw error;
    }
  },

  // End game session
  endGame: async (sessionId) => {
    try {
      const response = await apiClient.delete(`/game/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error ending game:', error);
      throw error;
    }
  },



// Combat endpoints
startCombat: async (sessionId, enemyType = 'random', enemyLevel = 1, enemyCount = 1) => {
  try {
    const response = await apiClient.post(`/game/${sessionId}/combat/start`, {
      enemy_type: enemyType,
      enemy_level: enemyLevel,
      enemy_count: enemyCount,
    });
    return response.data;
  } catch (error) {
    console.error('Error starting combat:', error);
    throw error;
  }
},

performCombatAction: async (sessionId, actionType, targetIndex = 0, abilityName = null, itemName = null) => {
  try {
    const response = await apiClient.post(`/game/${sessionId}/combat/action`, {
      action_type: actionType,
      target_index: targetIndex,
      ability_name: abilityName,
      item_name: itemName,
    });
    return response.data;
  } catch (error) {
    console.error('Error performing combat action:', error);
    throw error;
  }
},

getCombatStatus: async (sessionId) => {
  try {
    const response = await apiClient.get(`/game/${sessionId}/combat/status`);
    return response.data;
  } catch (error) {
    console.error('Error getting combat status:', error);
    throw error;
  }
},

endCombat: async (sessionId) => {
  try {
    const response = await apiClient.post(`/game/${sessionId}/combat/end`);
    return response.data;
  } catch (error) {
    console.error('Error ending combat:', error);
    throw error;
  }
},
};



export default apiClient;

