/**
 * CollectorTable - Enhanced with status badges and micro-interactions
 */

import { motion } from 'framer-motion';
import { useState } from 'react';
import type { CollectorConfig } from '../types';
import { Play, Globe, Clock, TrendingUp } from 'lucide-react';
import { apiClient } from '../api/client';
import { StatusBadge } from './StatusBadge';

interface CollectorTableProps {
  collectors: CollectorConfig[];
  onRefresh: () => void;
}

export function CollectorTable({ collectors, onRefresh }: CollectorTableProps) {
  const [triggering, setTriggering] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  const handleTriggerRun = async (collectorId: string) => {
    setTriggering(collectorId);
    try {
      await apiClient.triggerRun(collectorId);
      setTimeout(() => {
        onRefresh();
        setTriggering(null);
      }, 2000);
    } catch (error) {
      console.error('Failed to trigger run:', error);
      setTriggering(null);
    }
  };

  const formatTimeAgo = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes === 0) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="glass-panel rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Active Collectors</h2>
            <p className="text-sm text-slate-400 mt-1">
              {collectors.filter(c => c.is_active).length} of {collectors.length} collectors running
            </p>
          </div>
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-4 py-2 bg-teal-500/10 border border-teal-500/30 rounded-lg"
          >
            <div className="text-2xl font-bold text-teal-400">
              {collectors.reduce((sum, c) => sum + c.total_runs, 0)}
            </div>
            <div className="text-xs text-slate-400">Total Runs</div>
          </motion.div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-900/30">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">
                Status
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">
                Collector
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">
                Source
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">
                Performance
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">
                Last Run
              </th>
              <th className="px-6 py-4 text-center text-xs font-medium text-slate-400 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/30">
            {collectors.map((collector, index) => (
              <motion.tr
                key={collector.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                onMouseEnter={() => setHovered(collector.id)}
                onMouseLeave={() => setHovered(null)}
                className={`transition-colors ${
                  hovered === collector.id ? 'bg-slate-800/30' : ''
                }`}
              >
                {/* Status */}
                <td className="px-6 py-4">
                  <StatusBadge 
                    status={collector.status} 
                    pulse={collector.is_active}
                  />
                </td>

                {/* Name */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      collector.is_active 
                        ? 'bg-teal-500/10 border border-teal-500/30' 
                        : 'bg-slate-800/50 border border-slate-700/30'
                    }`}>
                      <Globe className={`w-5 h-5 ${
                        collector.is_active ? 'text-teal-400' : 'text-slate-500'
                      }`} />
                    </div>
                    <div>
                      <div className="font-medium text-white">{collector.name}</div>
                      <div className="text-xs text-slate-500">{collector.selectors.length} fields</div>
                    </div>
                  </div>
                </td>

                {/* URL */}
                <td className="px-6 py-4">
                  <div className="text-sm text-slate-400 max-w-xs truncate">
                    {collector.target_url}
                  </div>
                </td>

                {/* Performance */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-teal-400" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        {Math.round((collector.successful_runs / collector.total_runs) * 100)}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {collector.successful_runs}/{collector.total_runs} runs
                      </div>
                    </div>
                  </div>
                </td>

                {/* Last Run */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-500" />
                    <span className="text-sm text-slate-400">
                      {formatTimeAgo(collector.last_run_at)}
                    </span>
                  </div>
                </td>

                {/* Actions */}
                <td className="px-6 py-4 text-center">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleTriggerRun(collector.id)}
                    disabled={!collector.is_active || triggering === collector.id}
                    className={`p-2 rounded-lg transition-all ${
                      collector.is_active
                        ? 'bg-teal-500/10 hover:bg-teal-500/20 text-teal-400'
                        : 'bg-slate-800/50 text-slate-500 cursor-not-allowed'
                    }`}
                    title="Trigger run"
                  >
                    <Play
                      size={16}
                      className={triggering === collector.id ? 'animate-pulse' : ''}
                    />
                  </motion.button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty state */}
      {collectors.length === 0 && (
        <div className="p-12 text-center">
          <Globe className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No collectors configured yet</p>
        </div>
      )}
    </motion.div>
  );
}
