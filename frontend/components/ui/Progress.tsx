'use client';

import { HTMLAttributes, forwardRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Animated Progress Bar
interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'quantum' | 'gradient';
  animate?: boolean;
}

const ProgressBar = forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      value,
      max = 100,
      label,
      showValue = true,
      size = 'md',
      variant = 'quantum',
      animate = true,
      className,
      ...props
    },
    ref
  ) => {
    const [displayValue, setDisplayValue] = useState(animate ? 0 : value);
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    useEffect(() => {
      if (animate) {
        const timer = setTimeout(() => setDisplayValue(value), 100);
        return () => clearTimeout(timer);
      }
    }, [value, animate]);

    const sizeClasses = {
      sm: 'h-1',
      md: 'h-2',
      lg: 'h-3',
    };

    const getColor = (val: number) => {
      if (val >= 80) return 'from-green-500 to-green-400';
      if (val >= 60) return 'from-yellow-500 to-yellow-400';
      return 'from-red-500 to-red-400';
    };

    const variantClasses = {
      default: 'bg-zinc-600',
      quantum: 'bg-gradient-to-r from-quantum-500 to-quantum-400',
      gradient: `bg-gradient-to-r ${getColor(percentage)}`,
    };

    return (
      <div ref={ref} className={`w-full ${className || ''}`} {...props}>
        {(label || showValue) && (
          <div className="flex justify-between items-center mb-2">
            {label && <span className="text-sm text-zinc-400">{label}</span>}
            {showValue && (
              <span className={`text-sm font-mono font-medium ${
                percentage >= 80 ? 'text-green-400' : percentage >= 60 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {Math.round(percentage)}%
              </span>
            )}
          </div>
        )}
        <div className={`w-full bg-zinc-800 rounded-full overflow-hidden ${sizeClasses[size]}`}>
          <motion.div
            className={`h-full rounded-full ${variantClasses[variant]}`}
            initial={{ width: 0 }}
            animate={{ width: `${animate ? displayValue : percentage}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
      </div>
    );
  }
);

ProgressBar.displayName = 'ProgressBar';

// Score Orb - Circular progress indicator
interface ScoreOrbProps extends HTMLAttributes<HTMLDivElement> {
  score: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  label?: string;
  animate?: boolean;
}

const ScoreOrb = forwardRef<HTMLDivElement, ScoreOrbProps>(
  ({ score, size = 'md', label, animate = true, className, ...props }, ref) => {
    const [displayScore, setDisplayScore] = useState(animate ? 0 : score);

    useEffect(() => {
      if (animate) {
        const duration = 1000;
        const start = Date.now();
        const timer = setInterval(() => {
          const elapsed = Date.now() - start;
          const progress = Math.min(elapsed / duration, 1);
          setDisplayScore(Math.round(score * progress));
          if (progress >= 1) clearInterval(timer);
        }, 16);
        return () => clearInterval(timer);
      }
    }, [score, animate]);

    const sizeConfig = {
      sm: { container: 'w-16 h-16', text: 'text-xl', stroke: 4 },
      md: { container: 'w-24 h-24', text: 'text-3xl', stroke: 5 },
      lg: { container: 'w-32 h-32', text: 'text-4xl', stroke: 6 },
      xl: { container: 'w-40 h-40', text: 'text-5xl', stroke: 8 },
    };

    const config = sizeConfig[size];
    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (displayScore / 100) * circumference;

    const getColor = (val: number) => {
      if (val >= 80) return '#22c55e';
      if (val >= 60) return '#eab308';
      return '#ef4444';
    };

    const getLabel = (val: number) => {
      if (val >= 90) return 'Excellent';
      if (val >= 80) return 'Good';
      if (val >= 60) return 'Fair';
      return 'Poor';
    };

    return (
      <div
        ref={ref}
        className={`relative flex flex-col items-center ${className || ''}`}
        {...props}
      >
        <div className={`relative ${config.container}`}>
          <svg className="w-full h-full transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="50%"
              cy="50%"
              r={radius}
              fill="none"
              stroke="#27272a"
              strokeWidth={config.stroke}
            />
            {/* Progress circle */}
            <motion.circle
              cx="50%"
              cy="50%"
              r={radius}
              fill="none"
              stroke={getColor(displayScore)}
              strokeWidth={config.stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{
                filter: `drop-shadow(0 0 8px ${getColor(displayScore)}40)`,
              }}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span
              className={`font-mono font-bold ${config.text}`}
              style={{ color: getColor(displayScore) }}
            >
              {displayScore}
            </span>
          </div>
        </div>
        {label !== undefined ? (
          <span className="mt-2 text-sm text-zinc-400">{label}</span>
        ) : (
          <span className="mt-2 text-sm text-zinc-500">{getLabel(displayScore)}</span>
        )}
      </div>
    );
  }
);

ScoreOrb.displayName = 'ScoreOrb';

// Step Progress - Multi-step progress indicator
interface Step {
  label: string;
  description?: string;
}

interface StepProgressProps extends HTMLAttributes<HTMLDivElement> {
  steps: Step[];
  currentStep: number;
  variant?: 'default' | 'compact';
}

const StepProgress = forwardRef<HTMLDivElement, StepProgressProps>(
  ({ steps, currentStep, variant = 'default', className, ...props }, ref) => {
    return (
      <div ref={ref} className={`w-full ${className || ''}`} {...props}>
        <div className="flex items-center">
          {steps.map((step, index) => (
            <div key={index} className="flex-1 flex items-center">
              {/* Step indicator */}
              <div className="relative flex items-center justify-center">
                <motion.div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                    index < currentStep
                      ? 'bg-quantum-500 text-black'
                      : index === currentStep
                      ? 'bg-quantum-500/20 border-2 border-quantum-500 text-quantum-400'
                      : 'bg-zinc-800 text-zinc-500 border border-zinc-700'
                  }`}
                  initial={false}
                  animate={
                    index === currentStep
                      ? {
                          boxShadow: [
                            '0 0 0 0 rgba(34, 197, 94, 0.4)',
                            '0 0 0 10px rgba(34, 197, 94, 0)',
                          ],
                        }
                      : {}
                  }
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {index < currentStep ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </motion.div>
                {variant === 'default' && (
                  <div className="absolute top-10 left-1/2 -translate-x-1/2 whitespace-nowrap">
                    <p
                      className={`text-xs font-medium ${
                        index <= currentStep ? 'text-white' : 'text-zinc-500'
                      }`}
                    >
                      {step.label}
                    </p>
                  </div>
                )}
              </div>
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-2 bg-zinc-800 overflow-hidden">
                  <motion.div
                    className="h-full bg-quantum-500"
                    initial={{ width: 0 }}
                    animate={{ width: index < currentStep ? '100%' : '0%' }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }
);

StepProgress.displayName = 'StepProgress';

export { ProgressBar, ScoreOrb, StepProgress };
