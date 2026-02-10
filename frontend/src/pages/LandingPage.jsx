import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Sword, Skull, BookOpen, Scroll, ChevronRight, Sparkles } from 'lucide-react';

function LandingPage() {
  return (
    <div className="min-h-screen bg-linear-to-b from-black via-slate-950 to-purple-950 text-white overflow-hidden relative">
      
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-red-600 rounded-full opacity-10 blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-150 h-150 bg-blue-600 rounded-full opacity-5 blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Floating Particles */}
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-purple-400 rounded-full opacity-30"
          initial={{ 
            x: Math.random() * window.innerWidth, 
            y: Math.random() * window.innerHeight 
          }}
          animate={{ 
            y: [null, Math.random() * window.innerHeight],
            x: [null, Math.random() * window.innerWidth],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{ 
            duration: Math.random() * 10 + 10, 
            repeat: Infinity,
            ease: "linear"
          }}
        />
      ))}

      <div className="relative z-10 min-h-screen flex flex-col">
        
        {/* Navigation */}
        <motion.nav 
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="p-6 flex justify-between items-center border-b border-purple-900/30 backdrop-blur-sm"
        >
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles className="text-purple-400" size={32} />
            </motion.div>
            <h1 className="text-2xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
              AI Dungeon Master
            </h1>
          </div>
          
          <div className="hidden md:flex gap-6 items-center">
            <a href="#features" className="text-gray-300 hover:text-purple-400 transition text-sm">Features</a>
            <a href="#about" className="text-gray-300 hover:text-purple-400 transition text-sm">About</a>
            <Link 
              to="/create-character" 
              className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-full transition font-semibold text-sm"
            >
              Start Adventure
            </Link>
          </div>
        </motion.nav>

        {/* Hero Section */}
        <div className="flex-1 flex items-center justify-center px-6 py-20">
          <div className="max-w-6xl w-full">
            
            {/* Main Hero Content */}
            <div className="text-center space-y-8">
              
              {/* Title */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 1, delay: 0.2 }}
              >
                <motion.h1 
                  className="text-7xl md:text-9xl font-black mb-6"
                  style={{
                    fontFamily: "'Cinzel', serif",
                    textShadow: '0 0 40px rgba(168, 85, 247, 0.5), 0 0 80px rgba(168, 85, 247, 0.3)'
                  }}
                >
                  <span className="bg-linear-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
                    YOUR LEGEND
                  </span>
                  <br />
                  <span className="bg-linear-to-r from-red-400 via-orange-400 to-yellow-400 bg-clip-text text-transparent">
                    AWAITS
                  </span>
                </motion.h1>
                
                <motion.p 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed"
                  style={{ fontFamily: "'Crimson Text', serif" }}
                >
                  Enter a world where AI breathes life into your every choice. 
                  Battle fierce enemies, forge alliances, and carve your destiny 
                  in an ever-evolving narrative.
                </motion.p>
              </motion.div>

              {/* CTA Buttons */}
              <motion.div
                initial={{ y: 40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="flex flex-col sm:flex-row gap-4 justify-center items-center"
              >
                <Link to="/create-character">
                  <motion.button
                    whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(168, 85, 247, 0.6)' }}
                    whileTap={{ scale: 0.95 }}
                    className="group relative px-10 py-5 bg-linear-to-r from-purple-600 to-pink-600 rounded-2xl font-bold text-lg overflow-hidden shadow-2xl"
                  >
                    <div className="absolute inset-0 bg-linear-to-r from-purple-400 to-pink-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="relative flex items-center gap-3">
                      <Sword size={24} />
                      BEGIN YOUR QUEST
                      <ChevronRight size={24} className="group-hover:translate-x-1 transition-transform" />
                    </div>
                  </motion.button>
                </Link>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-10 py-5 border-2 border-purple-500 rounded-2xl font-semibold text-lg hover:bg-purple-500/20 transition"
                >
                  <div className="flex items-center gap-3">
                    <BookOpen size={24} />
                    LEARN MORE
                  </div>
                </motion.button>
              </motion.div>

              {/* Stats */}
              <motion.div
                initial={{ y: 40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 1 }}
                className="grid grid-cols-3 gap-8 max-w-3xl mx-auto mt-16 pt-16 border-t border-purple-900/30"
              >
                <div className="text-center">
                  <div className="text-4xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    ∞
                  </div>
                  <div className="text-sm text-gray-400 mt-2">Infinite Stories</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    100+
                  </div>
                  <div className="text-sm text-gray-400 mt-2">Unique Enemies</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    AI
                  </div>
                  <div className="text-sm text-gray-400 mt-2">Powered Narrative</div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <motion.section
          id="features"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1 }}
          viewport={{ once: true }}
          className="py-20 px-6 border-t border-purple-900/30"
        >
          <div className="max-w-7xl mx-auto">
            <h2 className="text-5xl font-bold text-center mb-16 bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Epic Features
            </h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  icon: <Sword size={40} />,
                  title: 'Dynamic Combat',
                  description: 'Engage in turn-based battles with intelligent AI enemies. Every fight is unique and challenging.'
                },
                {
                  icon: <Scroll size={40} />,
                  title: 'Living Narrative',
                  description: 'Your choices shape the story. AI crafts responses based on your decisions and playstyle.'
                },
                {
                  icon: <Skull size={40} />,
                  title: 'Character Growth',
                  description: 'Level up, gain abilities, and customize your hero with attributes, skills, and equipment.'
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ y: 50, opacity: 0 }}
                  whileInView={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.2 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -10, boxShadow: '0 20px 40px rgba(168, 85, 247, 0.3)' }}
                  className="bg-linear-to-br from-purple-900/20 to-pink-900/20 backdrop-blur-sm border border-purple-500/30 rounded-2xl p-8 text-center"
                >
                  <div className="inline-block p-4 bg-purple-600/20 rounded-full mb-4 text-purple-400">
                    {feature.icon}
                  </div>
                  <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* Footer CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="py-20 px-6 text-center border-t border-purple-900/30"
        >
          <h2 className="text-4xl md:text-6xl font-bold mb-6">
            Ready to Write Your Story?
          </h2>
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            Join thousands of adventurers in crafting legendary tales powered by AI.
          </p>
          <Link to="/create-character">
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: '0 0 40px rgba(168, 85, 247, 0.8)' }}
              whileTap={{ scale: 0.95 }}
              className="px-12 py-6 bg-linear-to-r from-purple-600 to-pink-600 rounded-full font-bold text-xl shadow-2xl"
            >
              Start Your Adventure Now
            </motion.button>
          </Link>
        </motion.div>

        {/* Footer */}
        <footer className="border-t border-purple-900/30 py-8 px-6 text-center text-gray-500 text-sm">
          <p>© 2025 AI Dungeon Master. Powered by Gemini AI & Anthropic Claude.</p>
        </footer>
      </div>

      {/* Add Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
      `}</style>
    </div>
  );
}

export default LandingPage;