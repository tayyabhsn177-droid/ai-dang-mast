import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { gameApi } from '../services/api';

function CombatView({ sessionId, onCombatEnd }) {
  const [combatData, setCombatData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(0);
  const [selectedAbility, setSelectedAbility] = useState(null);
  const [error, setError] = useState(null);
  const [damageAnimation, setDamageAnimation] = useState(null);

  const abilities = [
    { name: 'Power Strike', type: 'ability', icon: '⚔️', cost: '15 Stamina', description: 'High damage attack' },
    { name: 'Fireball', type: 'ability', icon: '🔥', cost: '20 Mana', description: 'Magical fire damage' },
    { name: 'Heal', type: 'ability', icon: '💚', cost: '25 Mana', description: 'Restore health' },
  ];

  useEffect(() => {
    loadCombatStatus();
  }, []);

  const loadCombatStatus = async () => {
    try {
      const response = await gameApi.getCombatStatus(sessionId);
      setCombatData(response);
      setIsLoading(false);
    } catch (err) {
      console.error('Failed to load combat status:', err);
      setError('Failed to load combat');
      setIsLoading(false);
    }
  };

  const handleCombatAction = async (actionType, abilityName = null, itemName = null) => {
    setActionLoading(true);
    setError(null);

    try {
      const response = await gameApi.performCombatAction(
        sessionId,
        actionType,
        selectedTarget,
        abilityName,
        itemName
      );

      console.log('Combat action response:', response);

      // Show damage animation
      if (actionType === 'attack' || actionType === 'ability') {
        setDamageAnimation({ target: selectedTarget, type: actionType });
        setTimeout(() => setDamageAnimation(null), 1000);
      }

      if (response.combat_ended) {
        if (response.victory) {
          const rewardText = `🎉 Victory!\n\nRewards:\n💫 ${response.rewards.xp} XP\n💰 ${response.rewards.gold} Gold${
            response.rewards.loot.length > 0 ? `\n🎁 Loot: ${response.rewards.loot.join(', ')}` : ''
          }${response.rewards.leveled_up ? `\n\n⭐ LEVEL UP! You are now level ${response.rewards.new_level}!` : ''}`;
          
          setTimeout(() => {
            alert(rewardText);
            onCombatEnd();
          }, 500);
        } else if (response.defeat) {
          setTimeout(() => {
            alert('💀 Defeat! You have fallen in battle...');
            onCombatEnd();
          }, 500);
        } else if (response.fled) {
          setTimeout(() => {
            alert('🏃 You successfully fled from combat!');
            onCombatEnd();
          }, 500);
        }
        return;
      }

      setCombatData(response);
      setSelectedAbility(null);

    } catch (err) {
      console.error('Failed to perform combat action:', err);
      setError(err.response?.data?.detail || 'Failed to perform action');
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-fantasy-dark flex items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-red-500 border-t-transparent mb-4 mx-auto"></div>
          <p className="text-xl text-gray-300">⚔️ Entering Combat...</p>
        </motion.div>
      </div>
    );
  }

  if (!combatData || !combatData.in_combat) {
    return (
      <div className="min-h-screen bg-fantasy-dark flex items-center justify-center">
        <p className="text-xl text-gray-300">Not in combat</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-fantasy-dark text-white p-4">
      <div className="max-w-7xl mx-auto">
        
        {/* Combat Header */}
        <motion.div 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-red-900 bg-opacity-30 border-2 border-red-500 rounded-lg p-4 mb-4"
        >
          <h1 className="text-3xl font-bold text-center text-red-400 animate-pulse">
            ⚔️ COMBAT MODE ⚔️
          </h1>
          <p className="text-center text-gray-300 mt-2">
            Turn Order: {combatData.turn_order?.join(' → ')}
          </p>
        </motion.div>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-red-900 bg-opacity-20 border-2 border-red-500 rounded-lg p-4 mb-4"
            >
              <p className="text-red-400">⚠️ {error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          
          {/* Left - Player Stats */}
          <motion.div 
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="lg:col-span-1"
          >
            <div className="bg-fantasy-darker rounded-lg p-4 border-2 border-blue-500 sticky top-4">
              <h2 className="text-xl font-bold mb-4 text-blue-400">👤 You</h2>

              {/* Health Bar */}
              <div className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-semibold">❤️ Health</span>
                  <span className="text-red-400">{combatData.player_stats.hp}/{combatData.player_stats.max_hp}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(combatData.player_stats.hp / combatData.player_stats.max_hp) * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-gradient-to-r from-red-600 to-red-500"
                  />
                </div>
              </div>

              {/* Mana Bar */}
              <div className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-semibold">✨ Mana</span>
                  <span className="text-blue-400">{combatData.player_stats.mana}/{combatData.player_stats.max_mana}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(combatData.player_stats.mana / combatData.player_stats.max_mana) * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-gradient-to-r from-blue-600 to-blue-500"
                  />
                </div>
              </div>

              {/* Stamina Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-semibold">⚡ Stamina</span>
                  <span className="text-orange-400">{combatData.player_stats.stamina}/{combatData.player_stats.max_stamina}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(combatData.player_stats.stamina / combatData.player_stats.max_stamina) * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-gradient-to-r from-orange-600 to-orange-500"
                  />
                </div>
              </div>

              {/* Status Effects */}
              {combatData.player_stats.status_effects && combatData.player_stats.status_effects.length > 0 && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-purple-900 bg-opacity-30 rounded-lg p-3 border border-purple-500"
                >
                  <h3 className="text-sm font-semibold mb-2 text-purple-400">💫 Status Effects</h3>
                  <div className="flex flex-wrap gap-2">
                    {combatData.player_stats.status_effects.map((effect, idx) => (
                      <motion.span 
                        key={idx}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="bg-purple-800 px-2 py-1 rounded text-xs animate-pulse"
                      >
                        {effect}
                      </motion.span>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Center - Enemies & Actions */}
          <div className="lg:col-span-2 space-y-4">
            
            {/* Enemies Grid */}
            <div>
              <h2 className="text-xl font-bold mb-3 text-red-400">👹 Enemies</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {combatData.enemies.map((enemy, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ 
                      opacity: 1, 
                      scale: selectedTarget === index ? 1.05 : 1,
                      x: damageAnimation?.target === index ? [0, -10, 10, -10, 10, 0] : 0
                    }}
                    transition={{ duration: 0.3 }}
                    onClick={() => setSelectedTarget(index)}
                    className={`bg-fantasy-darker rounded-lg p-4 border-2 cursor-pointer transition-all ${
                      selectedTarget === index
                        ? 'border-red-500 bg-red-900 bg-opacity-20 shadow-lg shadow-red-500/50'
                        : 'border-gray-700 hover:border-red-400'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-bold text-lg">{enemy.name}</h3>
                        <p className="text-xs text-gray-400">Level {enemy.level} {enemy.type}</p>
                        {enemy.is_boss && (
                          <motion.span 
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ repeat: Infinity, duration: 2 }}
                            className="inline-block bg-red-600 text-xs px-2 py-1 rounded mt-1"
                          >
                            👑 BOSS
                          </motion.span>
                        )}
                      </div>
                      {selectedTarget === index && (
                        <motion.span 
                          initial={{ scale: 0 }}
                          animate={{ scale: 1, rotate: 360 }}
                          className="text-2xl"
                        >
                          🎯
                        </motion.span>
                      )}
                    </div>

                    {/* Enemy Health Bar */}
                    <div className="mb-2">
                      <div className="flex justify-between text-sm mb-1">
                        <span>❤️ HP</span>
                        <span className="text-red-400">{enemy.hp}/{enemy.max_hp}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <motion.div 
                          animate={{ width: `${(enemy.hp / enemy.max_hp) * 100}%` }}
                          transition={{ duration: 0.5 }}
                          className="h-full bg-gradient-to-r from-red-600 to-red-500"
                        />
                      </div>
                    </div>

                    {/* Enemy Status Effects */}
                    {enemy.status_effects && enemy.status_effects.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {enemy.status_effects.map((effect, idx) => (
                          <span key={idx} className="bg-purple-800 px-2 py-0.5 rounded text-xs animate-pulse">
                            {effect}
                          </span>
                        ))}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Combat Actions */}
            <motion.div 
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-fantasy-darker rounded-lg p-4 border border-gray-800"
            >
              <h2 className="text-xl font-bold mb-4 text-fantasy-purple">⚡ Your Actions</h2>

              {/* Basic Actions */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleCombatAction('attack')}
                  disabled={actionLoading}
                  className="bg-red-700 hover:bg-red-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all shadow-lg"
                >
                  ⚔️ Attack
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedAbility('abilities')}
                  disabled={actionLoading}
                  className="bg-purple-700 hover:bg-purple-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all shadow-lg"
                >
                  ✨ Ability
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleCombatAction('defend')}
                  disabled={actionLoading}
                  className="bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all shadow-lg"
                >
                  🛡️ Defend
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleCombatAction('flee')}
                  disabled={actionLoading}
                  className="bg-yellow-700 hover:bg-yellow-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all shadow-lg"
                >
                  🏃 Flee
                </motion.button>
              </div>

              {/* Ability Selection */}
              <AnimatePresence>
                {selectedAbility === 'abilities' && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-gray-900 rounded-lg p-4 border border-purple-500 mb-4 overflow-hidden"
                  >
                    <h3 className="text-lg font-semibold mb-3 text-purple-400">Choose an Ability</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {abilities.map((ability, index) => (
                        <motion.button
                          key={index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleCombatAction('ability', ability.name)}
                          disabled={actionLoading}
                          className="bg-purple-800 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-left p-3 rounded-lg border border-purple-600 transition-all"
                        >
                          <div className="text-2xl mb-1">{ability.icon}</div>
                          <div className="font-semibold text-sm">{ability.name}</div>
                          <div className="text-xs text-purple-300">{ability.cost}</div>
                          <div className="text-xs text-gray-400 mt-1">{ability.description}</div>
                        </motion.button>
                      ))}
                    </div>
                    <button
                      onClick={() => setSelectedAbility(null)}
                      className="mt-3 text-sm text-gray-400 hover:text-white transition"
                    >
                      ← Back
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Loading State */}
              {actionLoading && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center text-gray-400 py-2"
                >
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-fantasy-purple border-t-transparent mr-2"></div>
                  <span className="animate-pulse">⚔️ Executing action...</span>
                </motion.div>
              )}
            </motion.div>

            {/* Combat Log */}
            <motion.div 
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-fantasy-darker rounded-lg p-4 border border-gray-800"
            >
              <h2 className="text-xl font-bold mb-3 text-fantasy-gold">📜 Combat Log</h2>
              <div className="bg-gray-900 rounded-lg p-3 h-64 overflow-y-auto space-y-1">
                {combatData.combat_log && combatData.combat_log.length > 0 ? (
                  combatData.combat_log.map((entry, index) => (
                    <motion.div 
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="text-sm text-gray-300 border-b border-gray-800 pb-1"
                    >
                      {entry}
                    </motion.div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No combat log yet...</p>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CombatView;