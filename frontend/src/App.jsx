import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import LandingPage from './pages/LandingPage';
import CharacterCreation from './components/CharacterCreation';
import GameScreen from './components/GameScreen';
import CombatView from './components/CombatView';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import { gameApi } from './services/api';

function App() {
  const [gameStarted, setGameStarted] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [gameData, setGameData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inCombat, setInCombat] = useState(false);

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
    setInCombat(false);
  };

  const handleCombatStart = () => {
    setInCombat(true);
  };

  const handleCombatEnd = () => {
    setInCombat(false);
  };

  return (
    <Router>
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Character Creation */}
        <Route 
          path="/create-character" 
          element={
            isLoading ? (
              <LoadingSpinner message="Creating your adventure..." />
            ) : error ? (
              <ErrorMessage error={error} onRetry={handleRetry} />
            ) : gameStarted ? (
              <Navigate to="/game" replace />
            ) : (
              <CharacterCreation onStartGame={handleStartGame} />
            )
          } 
        />
        
        {/* Main Game Screen */}
        <Route 
          path="/game" 
          element={
            !gameStarted || !sessionId ? (
              <Navigate to="/create-character" replace />
            ) : inCombat ? (
              <Navigate to="/combat" replace />
            ) : (
              <GameScreen 
                sessionId={sessionId} 
                initialGameData={gameData}
                onCombatStart={handleCombatStart}
              />
            )
          } 
        />
        
        {/* Combat Screen */}
        <Route 
          path="/combat" 
          element={
            !gameStarted || !sessionId ? (
              <Navigate to="/create-character" replace />
            ) : !inCombat ? (
              <Navigate to="/game" replace />
            ) : (
              <CombatView 
                sessionId={sessionId} 
                onCombatEnd={handleCombatEnd}
              />
            )
          } 
        />
        
        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;