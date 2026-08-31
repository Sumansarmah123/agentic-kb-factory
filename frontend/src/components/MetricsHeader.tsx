/**
 * MetricsHeader Component
 * Real-time dashboard metrics with Apple Design springs
 */

import { motion } from 'framer-motion';
import type { DashboardMetrics } from '../types';
import { Activity, Database, Shield, TrendingUp } from 'lucide-react';

interface MetricsHeaderProps {
  metrics: DashboardMetrics;
  loading?: boolean;
}

export function MetricsHeader({ metrics, loading }: MetricsHeaderProps) {
  const metricCards = [
    {
      label: 'Active Collectors',
      value: metrics.active_collectors,
      total: metrics.total_collectors,
      icon: Database,
      color: 'text-teal-400',
    },
    {
      label: 'Total Extractions',
      value: metrics.total_extractions,
      icon: Activity,
      color: 'text-indigo-400',
    },
    {
      label: 'Healing Events',
      value: metrics.healing_events,
      icon: Shield,
      color: 'text-purple-400',
    },
    {
      label: 'Success Rate',
      value: `${metrics.success_rate}%`,
      icon: TrendingUp,
      color: 'text-teal-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {metricCards.map((card, index) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            type: 'spring',
            damping: 25,
            stiffness: 300,
            delay: index * 0.05,
          }}
          className="glass-panel p-6 rounded-xl"
        >
          <div className="flex items-start justify-between mb-3">
            <div className={`p-2 rounded-lg bg-slate-800/50 ${card.color}`}>
              <card.icon size={20} />
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="text-2xl font-bold">
              {loading ? (
                <div className="h-8 w-20 bg-slate-800 animate-pulse rounded" />
              ) : (
                <span>
                  {card.value}
                  {card.total && (
                    <span className="text-slate-500 text-lg">/{card.total}</span>
                  )}
                </span>
              )}
            </div>
            <div className="text-sm text-slate-400">{card.label}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
