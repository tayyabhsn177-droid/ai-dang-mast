import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameApi } from '../services/api';
import { ArrowLeft, Menu } from 'lucide-react';

function GameScreen({ sessionId, initialGameData, onCombatStart }) {
    const navigate = useNavigate();
    const [gameData, setGameData] = useState(initialGameData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleAction = async (action) => {
        setIsLoading(true);
        setError(null);

        try {
            console.log('Taking action:', action);

            const response = await gameApi.takeAction(sessionId, action);
            console.log('Action response:', response);

            // Check for game over
            if (response.game_over) {
                alert(`Game Over!\n\n${response.message}\n\nFinal Level: ${response.final_stats?.level || 'N/A'}`);
                navigate('/');
                return;
            }

            // Update game data with new scene and actions
            setGameData({
                ...gameData,
                current_scene: response.current_scene,
                available_actions: response.available_actions,
                player_stats: response.player_stats,
                dice_roll: response.dice_roll,
                outcome: response.outcome,
            });

        } catch (err) {
            console.error('Failed to take action:', err);
            setError(err.response?.data?.detail || 'Failed to process action');
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartCombat = async () => {
        try {
            await gameApi.startCombat(sessionId, 'random', 1, 1);
            onCombatStart();
            navigate('/combat');
        } catch (err) {
            console.error('Failed to start combat:', err);
            setError('Failed to start combat');
        }
    };

    const handleBackToHome = () => {
        if (window.confirm('Are you sure you want to end your adventure?')) {
            navigate('/');
        }
    };

    return (
        <div className="min-h-screen bg-fantasy-dark text-white p-4">
            <div className="max-w-6xl mx-auto">

                {/* Header */}
                <div className="bg-fantasy-darker rounded-lg p-4 mb-4 border border-gray-800">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={handleBackToHome}
                                className="text-gray-400 hover:text-white transition"
                            >
                                <ArrowLeft size={24} />
                            </button>
                            <h1 className="text-2xl font-bold text-fantasy-gold">
                                🎲 AI Dungeon Master
                            </h1>
                        </div>
                        <div className="text-sm text-gray-400">
                            Session: {sessionId.slice(0, 8)}...
                        </div>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                    {/* Left Sidebar - Character Stats */}
                    <div className="lg:col-span-1">
                        <div className="bg-fantasy-darker rounded-lg p-4 border border-gray-800 sticky top-4">
                            <h2 className="text-xl font-bold mb-4 text-fantasy-purple">
                                ⚔️ Character
                            </h2>

                            {/* Health Bar */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-semibold">❤️ Health</span>
                                    <span>{gameData.player_stats.hp}/{gameData.player_stats.max_hp}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                                    <div
                                        className="h-full bg-red-500 transition-all duration-500"
                                        style={{ width: `${(gameData.player_stats.hp / gameData.player_stats.max_hp) * 100}%` }}
                                    />
                                </div>
                            </div>

                            {/* Mana Bar */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-semibold">✨ Mana</span>
                                    <span>{gameData.player_stats.mana}/{gameData.player_stats.max_mana}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 transition-all duration-500"
                                        style={{ width: `${(gameData.player_stats.mana / gameData.player_stats.max_mana) * 100}%` }}
                                    />
                                </div>
                            </div>

                            {/* Stamina Bar */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-semibold">⚡ Stamina</span>
                                    <span>{gameData.player_stats.stamina}/{gameData.player_stats.max_stamina}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                                    <div
                                        className="h-full bg-orange-500 transition-all duration-500"
                                        style={{ width: `${(gameData.player_stats.stamina / gameData.player_stats.max_stamina) * 100}%` }}
                                    />
                                </div>
                            </div>

                            {/* Level & XP */}
                            <div className="bg-gray-900 rounded-lg p-3 mb-4">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-semibold">📊 Level {gameData.player_stats.level}</span>
                                    <span className="text-xs text-gray-400">
                                        {gameData.player_stats.xp}/{gameData.player_stats.xp_to_next}
                                    </span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="h-full bg-fantasy-gold transition-all duration-500"
                                        style={{ width: `${(gameData.player_stats.xp / gameData.player_stats.xp_to_next) * 100}%` }}
                                    />
                                </div>
                            </div>

                            {/* Inventory */}
                            <div>
                                <h3 className="text-sm font-semibold mb-2 text-gray-400">🎒 Inventory</h3>
                                <div className="bg-gray-900 rounded-lg p-3 min-h-20">
                                    {gameData.player_stats.inventory && gameData.player_stats.inventory.length > 0 ? (
                                        <div className="flex flex-wrap gap-2">
                                            {gameData.player_stats.inventory.map((item, index) => (
                                                <span
                                                    key={index}
                                                    className="bg-gray-800 px-2 py-1 rounded text-xs border border-gray-700"
                                                >
                                                    {item}
                                                </span>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-500 text-sm">Empty</p>
                                    )}
                                </div>
                            </div>

                            {/* Last Roll Info */}
                            {gameData.dice_roll > 0 && (
                                <div className="mt-4 bg-gray-900 rounded-lg p-3 border-2 border-fantasy-purple">
                                    <div className="text-center">
                                        <div className="text-3xl mb-1">🎲</div>
                                        <div className="text-2xl font-bold text-fantasy-gold">{gameData.dice_roll}</div>
                                        <div className="text-xs text-gray-400 mt-1">
                                            {gameData.outcome === 'success' ? '✅ Success!' : '❌ Failure'}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Center - Story & Actions */}
                    <div className="lg:col-span-2">

                        {/* Current Scene */}
                        <div className="bg-fantasy-darker rounded-lg p-6 mb-4 border border-gray-800">
                            <h2 className="text-xl font-bold mb-4 text-fantasy-purple">📖 Current Scene</h2>
                            <div className="prose prose-invert max-w-none">
                                <p className="text-gray-300 whitespace-pre-line leading-relaxed">
                                    {gameData.current_scene}
                                </p>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-900 bg-opacity-20 border-2 border-red-500 rounded-lg p-4 mb-4">
                                <p className="text-red-400">⚠️ {error}</p>
                            </div>
                        )}

                        {/* Available Actions */}
                        <div className="bg-fantasy-darker rounded-lg p-6 border border-gray-800">
                            <h2 className="text-xl font-bold mb-4 text-fantasy-purple">⚡ What will you do?</h2>

                            <div className="grid grid-cols-1 gap-3">
                                {gameData.available_actions.map((action, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleAction(action)}
                                        disabled={isLoading}
                                        className="bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:cursor-not-allowed text-left p-4 rounded-lg border-2 border-gray-700 hover:border-fantasy-purple transition-all transform hover:scale-[1.02] disabled:transform-none group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-white group-hover:text-fantasy-gold transition">
                                                <span className="text-fantasy-purple font-bold mr-2">{index + 1}.</span>
                                                {action}
                                            </span>
                                            {isLoading ? (
                                                <div className="animate-spin rounded-full h-5 w-5 border-2 border-fantasy-purple border-t-transparent"></div>
                                            ) : (
                                                <span className="text-gray-600 group-hover:text-fantasy-purple transition">→</span>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {isLoading && (
                                <div className="mt-4 text-center text-gray-400 animate-pulse">
                                    🎲 Rolling the dice of fate...
                                </div>
                            )}
                        </div>
                        
                        {/* Combat Test Button */}
                        <div className="mt-4">
                            <button
                                onClick={handleStartCombat}
                                className="w-full bg-red-700 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg transition-all transform hover:scale-105"
                            >
                                ⚔️ Start Combat (Test)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default GameScreen;