/**
 * HealingLogs Component
 * Audit trail of all self-healing events
 */

import { motion } from 'framer-motion';
import { Shield, CheckCircle, XCircle, Code2 } from 'lucide-react';
import type { HealingEvent } from '../types';

interface HealingLogsProps {
  events: HealingEvent[];
}

export function HealingLogs({ events }: HealingLogsProps) {
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-teal-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center gap-3">
          <Shield size={24} className="text-teal-400" />
          <div>
            <h2 className="text-xl font-bold">Healing Event Log</h2>
            <p className="text-sm text-slate-400 mt-1">
              Autonomous selector repairs with audit trail
            </p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
        {events.map((event, index) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              type: 'spring',
              damping: 25,
              stiffness: 300,
              delay: index * 0.05,
            }}
            className="p-4 rounded-lg bg-slate-900/50 border border-slate-800/50"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                {event.status === 'success' ? (
                  <CheckCircle size={16} className="text-teal-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
                <span className="text-sm font-medium">{event.field_name}</span>
              </div>
              <div className="text-xs text-slate-500">
                {new Date(event.timestamp).toLocaleString()}
              </div>
            </div>

            <div className="space-y-2">
              {/* Old Selector */}
              <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
                <div className="text-xs text-red-400 mb-1 flex items-center gap-1">
                  <Code2 size={12} />
                  Old Selector (broken)
                </div>
                <code className="text-xs font-mono text-slate-300">
                  {event.old_selector}
                </code>
              </div>

              {/* New Selector */}
              <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded">
                <div className="text-xs text-teal-400 mb-1 flex items-center gap-1">
                  <Code2 size={12} />
                  New Selector (healed)
                </div>
                <code className="text-xs font-mono text-slate-300">
                  {event.new_selector}
                </code>
              </div>

              {/* Confidence & Reasoning */}
              <div className="flex items-center justify-between pt-2">
                <div className="text-xs text-slate-400">
                  Reasoning: {event.reasoning.slice(0, 100)}...
                </div>
                <div className={`text-xs font-medium ${getConfidenceColor(event.confidence_score)}`}>
                  {(event.confidence_score * 100).toFixed(0)}% confidence
                </div>
              </div>
            </div>
          </motion.div>
        ))}

        {events.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            <Shield size={48} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No healing events yet</p>
            <p className="text-xs mt-1">The system will autonomously repair broken selectors</p>
          </div>
        )}
      </div>
    </div>
  );
}
