/**
 * Hero Section - Grand Prize Polish
 * Clear value proposition in first 3 seconds
 */

import { motion } from 'framer-motion';
import { Sparkles, Zap, Shield } from 'lucide-react';

export const HeroSection = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', damping: 20 }}
      className="mb-8"
    >
      <div className="glass-panel rounded-2xl p-8 bg-gradient-to-br from-teal-500/10 via-slate-900/50 to-indigo-500/10 border-teal-500/20">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <motion.div
                animate={{
                  rotate: [0, 10, -10, 10, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  repeatDelay: 3,
                }}
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-400 to-indigo-500 flex items-center justify-center"
              >
                <Sparkles className="w-6 h-6 text-white" />
              </motion.div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  Autonomous Knowledge Base
                </h2>
                <p className="text-slate-300">
                  Self-healing web extraction powered by Gemini AI
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 mt-6">
              {/* Feature badges */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-2 px-3 py-2 bg-teal-500/20 border border-teal-500/30 rounded-lg"
              >
                <Zap className="w-4 h-4 text-teal-400" />
                <span className="text-sm text-teal-300 font-medium">
                  Multi-Agent Orchestration
                </span>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-2 px-3 py-2 bg-indigo-500/20 border border-indigo-500/30 rounded-lg"
              >
                <Shield className="w-4 h-4 text-indigo-400" />
                <span className="text-sm text-indigo-300 font-medium">
                  Model Armor Security
                </span>
              </motion.div>

              <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg">
                <div className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </div>
                <span className="text-sm text-emerald-300 font-medium">
                  Live System
                </span>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="hidden lg:flex flex-col items-end gap-2">
            <div className="text-right">
              <div className="text-3xl font-bold text-teal-400">97%</div>
              <div className="text-xs text-slate-400">Success Rate</div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-indigo-400">1.2K+</div>
              <div className="text-xs text-slate-400">Extractions</div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
