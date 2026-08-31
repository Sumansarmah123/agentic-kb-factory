/**
 * Live Activity Feed - Shows AI agents working in real-time
 * WOW FACTOR: Demonstrates autonomous multi-agent orchestration
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Zap, CheckCircle, AlertCircle, Brain } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ActivityItem {
  id: string;
  agent: 'Collector' | 'Healer';
  action: string;
  status: 'success' | 'analyzing' | 'healing' | 'failed';
  confidence?: number;
  timestamp: Date;
}

export const LiveActivityFeed = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([
    {
      id: '1',
      agent: 'Collector',
      action: 'Extracted 30 items from Hacker News',
      status: 'success',
      timestamp: new Date(Date.now() - 8 * 60 * 1000),
    },
    {
      id: '2',
      agent: 'Healer',
      action: 'Analyzing failed selector for GitHub Trending',
      status: 'analyzing',
      confidence: 0.94,
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
    },
    {
      id: '3',
      agent: 'Healer',
      action: 'Applied fix with 96% confidence - validation passed',
      status: 'success',
      confidence: 0.96,
      timestamp: new Date(Date.now() - 23 * 60 * 1000),
    },
  ]);

  // Simulate real-time activity (for demo)
  useEffect(() => {
    const interval = setInterval(() => {
      const newActivities: ActivityItem[] = [
        {
          id: Date.now().toString(),
          agent: 'Collector',
          action: 'Extracted 25 items from GitHub Trending',
          status: 'success',
          timestamp: new Date(),
        },
        {
          id: (Date.now() + 1).toString(),
          agent: 'Healer',
          action: 'Detected DOM structure change - healing initiated',
          status: 'healing',
          confidence: 0.89,
          timestamp: new Date(),
        },
      ];

      setActivities(prev => [
        newActivities[Math.floor(Math.random() * newActivities.length)],
        ...prev.slice(0, 4),
      ]);
    }, 12000); // New activity every 12 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-teal-400" />;
      case 'analyzing':
        return <Brain className="w-4 h-4 text-indigo-400 animate-pulse" />;
      case 'healing':
        return <Zap className="w-4 h-4 text-amber-400 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Activity className="w-4 h-4 text-slate-400" />;
    }
  };

  const getAgentColor = (agent: string) => {
    return agent === 'Collector' ? 'text-teal-400' : 'text-indigo-400';
  };

  const formatTimestamp = (date: Date) => {
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes === 0) return 'Just now';
    if (minutes === 1) return '1 min ago';
    return `${minutes} min ago`;
  };

  return (
    <div className="glass-panel rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center">
          <Activity className="w-5 h-5 text-teal-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Live Agent Activity</h3>
          <p className="text-sm text-slate-400">Real-time multi-agent orchestration</p>
        </div>
      </div>

      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {activities.map((activity) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{
                type: 'spring',
                stiffness: 500,
                damping: 30,
              }}
              className="flex items-start gap-3 p-4 bg-slate-800/30 rounded-xl border border-slate-700/30 hover:bg-slate-800/50 transition-colors"
            >
              <div className="mt-1">{getStatusIcon(activity.status)}</div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-sm font-medium ${getAgentColor(activity.agent)}`}>
                    {activity.agent} Agent
                  </span>
                  {activity.confidence && (
                    <span className="text-xs px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-full">
                      {Math.round(activity.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-300">{activity.action}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {formatTimestamp(activity.timestamp)}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Pulse indicator */}
      <div className="flex items-center gap-2 mt-6 pt-4 border-t border-slate-700/30">
        <div className="relative flex items-center">
          <span className="flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
          </span>
        </div>
        <span className="text-xs text-slate-400">System active - agents monitoring</span>
      </div>
    </div>
  );
};
