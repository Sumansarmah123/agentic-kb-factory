/**
 * ArchitectureModal Component
 * Shows system architecture with translucent material (Apple Design)
 */

import { motion, AnimatePresence } from 'framer-motion';
import { X, GitBranch } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ArchitectureModal({ isOpen, onClose }: ArchitectureModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{
              type: 'spring',
              damping: 25,
              stiffness: 300,
            }}
            className="fixed inset-x-4 top-20 mx-auto max-w-4xl z-50"
          >
            <div className="glass-panel rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <GitBranch size={24} className="text-teal-400" />
                  <h2 className="text-xl font-bold">System Architecture</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="bg-slate-900 rounded-lg p-6 font-mono text-xs leading-relaxed overflow-x-auto">
                <pre className="text-slate-300">
{`┌─────────────────────────────────────────────┐
│     Browser (React + Apple Design)          │
│  Dashboard | SelfHealingDemo | HealingLogs  │
└─────────────────┬───────────────────────────┘
                  │ HTTPS/REST
                  ↓
┌─────────────────────────────────────────────┐
│    FastAPI Backend (Google Cloud Run)       │
│  • Rate Limiting (10 req/min)               │
│  • Model Armor (security validation)        │
│  • OpenTelemetry (Cloud Trace)              │
└──────┬──────────────────────┬───────────────┘
       │                      │
   ┌───↓────┐          ┌─────↓─────┐
   │Firestore│         │Gemini 2.5 │
   │(State)  │         │  (Healing)│
   └────┬────┘          └─────┬─────┘
        │                     │
   ┌────↓─────────────────────↓────┐
   │    ADK Multi-Agent System      │
   │  Collector → Pub/Sub → Healer  │
   └────────────────────────────────┘

Flow:
1. User triggers extraction via Dashboard
2. Collector Agent extracts with BeautifulSoup
3. If 0 items → Pub/Sub event to Healer
4. Healer calls Gemini for new selector
5. New selector applied → retry extraction
6. Success logged to Firestore + traced
`}
                </pre>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-900/50 rounded-lg">
                  <div className="text-sm font-medium text-teal-400 mb-2">Key Technologies</div>
                  <ul className="text-xs space-y-1 text-slate-400">
                    <li>• Gemini 2.5 Flash (AI)</li>
                    <li>• Google ADK (Multi-agent)</li>
                    <li>• Cloud Run (Serverless)</li>
                    <li>• Firestore (State)</li>
                  </ul>
                </div>
                <div className="p-4 bg-slate-900/50 rounded-lg">
                  <div className="text-sm font-medium text-indigo-400 mb-2">Enterprise Features</div>
                  <ul className="text-xs space-y-1 text-slate-400">
                    <li>• Model Armor (Security)</li>
                    <li>• OpenTelemetry (Observability)</li>
                    <li>• Rate Limiting</li>
                    <li>• Audit Logging</li>
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
