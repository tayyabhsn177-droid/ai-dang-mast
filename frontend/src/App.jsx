import { useState } from 'react';
import CharacterCreation from './components/CharacterCreation';
import GameScreen from './components/GameScreen';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import { gameApi } from './services/api';

function App() {
  const [gameStarted, setGameStarted] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [gameData, setGameData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleStartGame = async (characterData) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('Starting game with:', characterData);
      
      const response = await gameApi.startGame(
        characterData.playerName,
        characterData.characterClass,
        characterData.setting
      );

      console.log('Game started successfully:', response);

      setSessionId(response.session_id);
      setGameData(response);
      setGameStarted(true);

    } catch (err) {
      console.error('Failed to start game:', err);
      setError({
        message: err.response?.data?.detail || 'Failed to connect to game server. Make sure your backend is running on http://localhost:8000'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    setGameStarted(false);
    setSessionId(null);
    setGameData(null);
  };

  if (isLoading) {
    return <LoadingSpinner message="Creating your adventure..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={handleRetry} />;
  }

  if (!gameStarted) {
    return <CharacterCreation onStartGame={handleStartGame} />;
  }

  return <GameScreen sessionId={sessionId} initialGameData={gameData} />;
}

export default App;