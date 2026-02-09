import { useState } from 'react';
import { Sword, WandSparkles, Shield,Sparkles , AlertTriangle} from "lucide-react";



function CharacterCreation({ onStartGame }) {
    const [playerName, setPlayerName] = useState('');
    const [characterClass, setCharacterClass] = useState('Warrior');
    const [setting, setSetting] = useState('Dark Fantasy Medieval Kingdom');

    const classes = [
        {
            name: 'Warrior',
            icon: Sword,
            description: 'Strong melee fighter'
        },
        {
            name: 'Mage',
            icon: WandSparkles,
            description: 'Master of arcane magic'
        },
        {
            name: 'Rogue',
            icon: Shield,
            description: 'Stealthy and cunning'
        },
        {
            name: 'Cleric',
            icon: Sparkles,
            description: 'Divine healer and support'
        },
    ];


    const settings = [
        'Dark Fantasy Medieval Kingdom',
        'Ancient Egyptian Desert',
        'Futuristic Cyberpunk City',
        'Mystical Enchanted Forest',
    ];

    const handleSubmit = (e) => {
        e.preventDefault();
        if (playerName.trim()) {
            onStartGame({
                playerName: playerName.trim(),
                characterClass,
                setting,
            });
        }
    };

    return (
        <div className="min-h-screen bg-fantasy-dark flex items-center justify-center p-4">
            <div className="max-w-2xl w-full">
                {/* Title */}
                <div className="text-center mb-8">
                    <h1 className="text-5xl font-bold text-fantasy-gold mb-2">
                        🎲 AI Dungeon Master
                    </h1>
                    <p className="text-gray-400">Create your character and begin your adventure</p>
                </div>

                {/* Form Card */}
                <div className="bg-fantasy-darker rounded-lg shadow-2xl p-8 border border-gray-800">
                    <form onSubmit={handleSubmit} className="space-y-6">

                        {/* Character Name */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-300 mb-2">
                                Character Name
                            </label>
                            <input
                                type="text"
                                value={playerName}
                                onChange={(e) => setPlayerName(e.target.value)}
                                placeholder="Enter your hero's name..."
                                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-fantasy-purple focus:ring-2 focus:ring-fantasy-purple focus:ring-opacity-50 transition"
                                maxLength={50}
                                required
                            />
                        </div>

                        {/* Character Class */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-300 mb-3">
                                Choose Your Class
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                {classes.map((cls) => (
                                    <button
                                        key={cls.name}
                                        type="button"
                                        onClick={() => setCharacterClass(cls.name)}
                                        className={`p-4 rounded-lg border-2 transition-all ${characterClass === cls.name
                                                ? 'border-fantasy-purple bg-fantasy-purple bg-opacity-20 shadow-lg'
                                                : 'border-gray-700 bg-gray-900 hover:border-gray-600'
                                            }`}
                                    >
                                        <div className="mb-2 flex justify-center">
                                            {(() => {
                                                const Icon = cls.icon;
                                                return <Icon size={32} className="text-fantasy-purple" />;
                                            })()}
                                        </div>

                                        <div className="font-semibold text-white">{cls.name}</div>
                                        <div className="text-xs text-gray-400 mt-1">{cls.description}</div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Setting */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-300 mb-2">
                                Choose Your World
                            </label>
                            <select
                                value={setting}
                                onChange={(e) => setSetting(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-fantasy-purple focus:ring-2 focus:ring-fantasy-purple focus:ring-opacity-50 transition"
                            >
                                {settings.map((s) => (
                                    <option key={s} value={s}>
                                        {s}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Submit Button */}
       <button
  type="submit"
  disabled={!playerName.trim()}
  className="w-full bg-fantasy-purple hover:bg-opacity-90 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-lg transition-all transform hover:scale-105 disabled:transform-none shadow-lg flex items-center justify-center gap-2"
>
  {playerName.trim() ? (
    <>
      <Sword size={20} />
      Begin Adventure
    </>
  ) : (
    <>
      <AlertTriangle size={20} />
      Enter Your Name First
    </>
  )}
</button>

                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-gray-500 text-sm mt-6">
                    Your choices shape your destiny
                </p>
            </div>
        </div>
    );
}

export default CharacterCreation;