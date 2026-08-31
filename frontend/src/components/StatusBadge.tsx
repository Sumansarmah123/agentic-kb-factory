/**
 * Status Badge - Animated status indicators
 */

import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Clock, Zap } from 'lucide-react';

interface StatusBadgeProps {
  status: 'healthy' | 'warning' | 'error' | 'active' | 'healing';
  label?: string;
  showIcon?: boolean;
  pulse?: boolean;
}

export const StatusBadge = ({ status, label, showIcon = true, pulse = false }: StatusBadgeProps) => {
  const configs = {
    healthy: {
      icon: CheckCircle,
      color: 'text-teal-400',
      bg: 'bg-teal-500/20',
      border: 'border-teal-500/30',
      text: label || 'Healthy',
    },
    warning: {
      icon: AlertCircle,
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
      border: 'border-amber-500/30',
      text: label || 'Warning',
    },
    error: {
      icon: AlertCircle,
      color: 'text-red-400',
      bg: 'bg-red-500/20',
      border: 'border-red-500/30',
      text: label || 'Error',
    },
    active: {
      icon: Clock,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/20',
      border: 'border-indigo-500/30',
      text: label || 'Active',
    },
    healing: {
      icon: Zap,
      color: 'text-purple-400',
      bg: 'bg-purple-500/20',
      border: 'border-purple-500/30',
      text: label || 'Healing',
    },
  };

  const config = configs[status];
  const Icon = config.icon;

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`inline-flex items-center gap-2 px-3 py-1.5 ${config.bg} border ${config.border} rounded-lg`}
    >
      {showIcon && (
        <Icon className={`w-3.5 h-3.5 ${config.color} ${pulse ? 'animate-pulse' : ''}`} />
      )}
      <span className={`text-xs font-medium ${config.color}`}>
        {config.text}
      </span>
    </motion.div>
  );
};
