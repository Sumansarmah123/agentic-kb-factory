/**
 * Sign-In Component with Hardcoded Credentials
 * Apple Design: Translucent modal with spring animation
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { LogIn, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const SignIn = () => {
  const { signIn } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const success = await signIn(username, password);
      if (!success) {
        setError('Invalid credentials. Try: Admin123 / Hackathon123');
      }
    } catch (err) {
      setError('Sign in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setUsername('Admin123');
    setPassword('Hackathon123');
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-teal-500/5 via-slate-950 to-indigo-500/5" />
      
      {/* Sign-in modal */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{
          type: "spring",
          stiffness: 260,
          damping: 20
        }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Translucent card */}
        <div className="bg-slate-900/40 backdrop-blur-apple border border-slate-800/50 rounded-3xl p-8 shadow-2xl">
          {/* Logo/Title */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1, type: "spring" }}
              className="inline-flex items-center justify-center w-16 h-16 bg-teal-500/10 rounded-2xl mb-4"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-500 rounded-lg" />
            </motion.div>
            
            <motion.h1
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="text-3xl font-semibold text-white mb-2"
            >
              Agentic KB Factory
            </motion.h1>
            
            <motion.p
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3, type: "spring" }}
              className="text-slate-400"
            >
              Self-healing knowledge base with autonomous agents
            </motion.p>
          </div>

          {/* Sign-in form */}
          <motion.form
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, type: "spring" }}
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            {/* Username field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-transparent transition-all"
                placeholder="Enter username"
                required
              />
            </div>

            {/* Password field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-transparent transition-all"
                placeholder="Enter password"
                required
              />
            </div>

            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm"
              >
                <AlertCircle size={16} />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Sign-in button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-500 hover:bg-teal-400 disabled:bg-slate-700 text-white font-medium py-3 px-6 rounded-xl flex items-center justify-center gap-3 transition-all duration-200 shadow-lg hover:shadow-xl active:scale-[0.98] disabled:cursor-not-allowed"
            >
              <LogIn className="w-5 h-5" />
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            {/* Demo credentials button */}
            <button
              type="button"
              onClick={fillDemoCredentials}
              className="w-full bg-slate-800/50 hover:bg-slate-700/50 text-slate-300 font-medium py-3 px-6 rounded-xl transition-all duration-200 active:scale-[0.98]"
            >
              Use Demo Credentials
            </button>
          </motion.form>

          {/* Footer with demo credentials */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-6 p-4 bg-teal-500/10 border border-teal-500/30 rounded-xl"
          >
            <p className="text-sm text-teal-400 font-medium mb-2">Demo Credentials:</p>
            <p className="text-sm text-slate-300 font-mono">
              Username: <span className="text-teal-400">Admin123</span>
            </p>
            <p className="text-sm text-slate-300 font-mono">
              Password: <span className="text-teal-400">Hackathon123</span>
            </p>
          </motion.div>

          {/* Hackathon footer */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-center text-sm text-slate-500 mt-6"
          >
            Built for All Things Agentic Hackathon
          </motion.p>
        </div>

        {/* Glow effect */}
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-teal-500/20 to-indigo-500/20 rounded-3xl blur-3xl opacity-30" />
      </motion.div>
    </div>
  );
};
