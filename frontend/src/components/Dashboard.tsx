/**
 * Dashboard Component - Grand Prize Polish
 * Hero section, live activity, visual hierarchy
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, GitBranch, LogOut, User } from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import type { CollectorConfig, HealingEvent, DashboardMetrics } from '../types';
import { HeroSection } from './HeroSection';
import { MetricsHeader } from './MetricsHeader';
import { CollectorTable } from './CollectorTable';
import { SelfHealingDemo } from './SelfHealingDemo';
import { HealingLogs } from './HealingLogs';
import { ArchitectureModal } from './ArchitectureModal';
import { LiveActivityFeed } from './LiveActivityFeed';
import { ModelArmorDemo } from './ModelArmorDemo';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    total_collectors: 0,
    active_collectors: 0,
    total_extractions: 0,
    healing_events: 0,
    success_rate: 0,
  });
  const [collectors, setCollectors] = useState<CollectorConfig[]>([]);
  const [healingEvents, setHealingEvents] = useState<HealingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [architectureOpen, setArchitectureOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [metricsData, collectorsData, healingData] = await Promise.all([
        apiClient.getDashboardMetrics(),
        apiClient.listCollectors(),
        apiClient.getHealingLogs(undefined, 50),
      ]);

      setMetrics(metricsData);
      setCollectors(collectorsData.collectors);
      setHealingEvents(healingData.events);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Toolbar with translucent blur */}
      <div className="toolbar">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <span className="text-xl font-bold">⚡</span>
            </div>
            <div>
              <h1 className="text-lg font-bold">Agentic KB Factory</h1>
              <p className="text-xs text-slate-400">Self-Healing DOM Engine</p>
            </div>
          </motion.div>

          <div className="flex items-center gap-3">
            {/* User badge */}
            {user && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/40 backdrop-blur-sm rounded-lg border border-slate-700/50 hover:border-teal-500/30 transition-colors cursor-pointer"
              >
                <User size={16} className="text-teal-400" />
                <span className="text-sm text-slate-300">{user.username}</span>
              </motion.div>
            )}

            <motion.button
              whileTap={{ scale: 0.95 }}
              whileHover={{ scale: 1.05 }}
              onClick={() => setArchitectureOpen(true)}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              <GitBranch size={14} />
              Architecture
            </motion.button>
            
            <motion.button
              whileTap={{ scale: 0.95 }}
              whileHover={{ scale: 1.05 }}
              onClick={loadData}
              disabled={loading}
              className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
            >
              <motion.div
                animate={loading ? { rotate: 360 } : {}}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              >
                <RefreshCw size={14} />
              </motion.div>
              Refresh
            </motion.button>

            <motion.button
              whileTap={{ scale: 0.95 }}
              whileHover={{ scale: 1.05 }}
              onClick={handleLogout}
              className="btn-secondary text-sm flex items-center gap-2"
              title="Sign out"
            >
              <LogOut size={14} />
            </motion.button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        {/* Hero Section - Clear Value Prop */}
        <HeroSection />

        {/* Metrics */}
        <MetricsHeader metrics={metrics} loading={loading} />

        {/* Two-column layout for Activity Feed and Self-Healing Demo */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Live Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <LiveActivityFeed />
          </motion.div>

          {/* Self-Healing Demo */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <SelfHealingDemo />
          </motion.div>
        </div>

        {/* NEW: Model Armor Demo - CRITICAL FOR GRAND PRIZE */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <ModelArmorDemo />
        </motion.div>

        {/* Collectors Table */}
        <div className="mb-8">
          <CollectorTable collectors={collectors} onRefresh={loadData} />
        </div>

        {/* Healing Logs */}
        <HealingLogs events={healingEvents} />
      </div>

      {/* Architecture Modal */}
      <ArchitectureModal
        isOpen={architectureOpen}
        onClose={() => setArchitectureOpen(false)}
      />
    </div>
  );
}
