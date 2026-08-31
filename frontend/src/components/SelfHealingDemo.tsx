/**
 * SelfHealingDemo Component - KEY INNOVATION
 * Shows real-time self-healing flow with Apple Design springs
 * State machine: idle → extracting → failure → healing → retrying → success
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { AlertCircle, Bot, CheckCircle, Loader, Sparkles } from 'lucide-react';

type HealingState = 'idle' | 'extracting' | 'failure' | 'healing' | 'retrying' | 'success';

interface HealingStep {
  state: HealingState;
  message: string;
  timestamp: Date;
}

export function SelfHealingDemo() {
  const [currentState, setCurrentState] = useState<HealingState>('idle');
  const [steps, setSteps] = useState<HealingStep[]>([]);
  const [confidenceScore, setConfidenceScore] = useState<number | null>(null);
  const [newSelector, setNewSelector] = useState<string | null>(null);

  // Simulate healing flow (in production, this would be real API calls)
  const startDemoFlow = () => {
    setSteps([]);
    setConfidenceScore(null);
    setNewSelector(null);
    
    // Step 1: Extracting
    setTimeout(() => {
      setCurrentState('extracting');
      addStep('extracting', 'Collector Agent running extraction...');
    }, 500);

    // Step 2: Failure detected
    setTimeout(() => {
      setCurrentState('failure');
      addStep('failure', '0 items extracted - Selector broken!');
    }, 2000);

    // Step 3: Healing initiated
    setTimeout(() => {
      setCurrentState('healing');
      addStep('healing', 'Healer Agent analyzing DOM with Gemini...');
    }, 3000);

    // Step 4: New selector suggested
    setTimeout(() => {
      const score = 0.92;
      const selector = 'div.content > article.post';
      setConfidenceScore(score);
      setNewSelector(selector);
      addStep('healing', `New selector: ${selector} (${(score * 100).toFixed(0)}% confidence)`);
    }, 5000);

    // Step 5: Retrying
    setTimeout(() => {
      setCurrentState('retrying');
      addStep('retrying', 'Applying new selector and retrying...');
    }, 6000);

    // Step 6: Success
    setTimeout(() => {
      setCurrentState('success');
      addStep('success', '12 items extracted - Self-healing successful! ✨');
    }, 7500);

    // Reset after demo
    setTimeout(() => {
      setCurrentState('idle');
    }, 10000);
  };

  const addStep = (state: HealingState, message: string) => {
    setSteps(prev => [...prev, { state, message, timestamp: new Date() }]);
  };

  const stateConfig = {
    idle: {
      icon: Sparkles,
      color: 'text-slate-400',
      bg: 'bg-slate-800/50',
      label: 'Ready',
    },
    extracting: {
      icon: Loader,
      color: 'text-teal-400',
      bg: 'bg-teal-500/20',
      label: 'Extracting',
    },
    failure: {
      icon: AlertCircle,
      color: 'text-red-400',
      bg: 'bg-red-500/20',
      label: 'Failure Detected',
    },
    healing: {
      icon: Bot,
      color: 'text-teal-400',
      bg: 'bg-teal-500/20',
      label: 'Self-Healing',
    },
    retrying: {
      icon: Loader,
      color: 'text-teal-400',
      bg: 'bg-teal-500/20',
      label: 'Retrying',
    },
    success: {
      icon: CheckCircle,
      color: 'text-teal-400',
      bg: 'bg-teal-500/20',
      label: 'Success',
    },
  };

  const config = stateConfig[currentState];
  const Icon = config.icon;

  return (
    <div className="glass-panel rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold">Self-Healing DOM Engine</h2>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous selector repair with Gemini AI
          </p>
        </div>
        
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={startDemoFlow}
          disabled={currentState !== 'idle'}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {currentState === 'idle' ? 'Run Demo' : 'Running...'}
        </motion.button>
      </div>

      {/* State Indicator */}
      <div className="mb-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentState}
            initial={{ opacity: 0, scale: 0.9, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{
              type: 'spring',
              damping: 25,
              stiffness: 300,
            }}
            className={`flex items-center gap-3 p-4 rounded-lg ${config.bg}`}
          >
            <motion.div
              animate={
                currentState === 'extracting' || currentState === 'retrying' || currentState === 'healing'
                  ? { rotate: 360 }
                  : {}
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
            >
              <Icon size={24} className={config.color} />
            </motion.div>
            <div className="flex-1">
              <div className={`font-medium ${config.color}`}>{config.label}</div>
              {currentState === 'healing' && confidenceScore && (
                <div className="text-xs text-slate-400 mt-1">
                  Confidence: {(confidenceScore * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Healing Steps Log */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        <AnimatePresence>
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{
                type: 'spring',
                damping: 25,
                stiffness: 300,
              }}
              className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/50 border border-slate-800/50"
            >
              <div className="text-xs text-slate-500 min-w-[60px]">
                {step.timestamp.toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </div>
              <div className="flex-1 text-sm">
                {step.message}
                {step.state === 'failure' && (
                  <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                    Old selector: <code className="font-mono">div.old-content &gt; p</code>
                  </div>
                )}
                {step.state === 'healing' && newSelector && (
                  <div className="mt-2 p-2 bg-teal-500/10 border border-teal-500/20 rounded text-xs text-teal-400">
                    New selector: <code className="font-mono">{newSelector}</code>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {steps.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            <Bot size={48} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">Click "Run Demo" to see self-healing in action</p>
          </div>
        )}
      </div>
    </div>
  );
}
