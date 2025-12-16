'use client';

import { forwardRef, InputHTMLAttributes, TextareaHTMLAttributes, useState } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, AnimatePresence } from 'framer-motion';

const inputVariants = cva(
  'w-full bg-zinc-900/80 border text-white placeholder:text-zinc-500 transition-all duration-200 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default: 'border-zinc-700 focus:border-quantum-500 focus:ring-2 focus:ring-quantum-500/20',
        terminal: 'border-zinc-700 focus:border-quantum-500 focus:ring-2 focus:ring-quantum-500/20 font-mono pl-8',
        ghost: 'border-transparent bg-zinc-800/50 focus:bg-zinc-800 focus:border-zinc-700',
        error: 'border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500/20',
      },
      inputSize: {
        sm: 'text-sm px-3 py-2 rounded-lg',
        md: 'text-sm px-4 py-3 rounded-lg',
        lg: 'text-base px-4 py-3.5 rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'default',
      inputSize: 'md',
    },
  }
);

export interface InputProps
  extends InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  showTerminalPrefix?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, inputSize, label, error, icon, showTerminalPrefix, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-zinc-400">{label}</label>
        )}
        <div className="relative">
          {showTerminalPrefix && (
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-quantum-500 font-mono font-bold">
              &gt;
            </span>
          )}
          {icon && !showTerminalPrefix && (
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            className={inputVariants({
              variant: error ? 'error' : variant,
              inputSize,
              className: `${icon && !showTerminalPrefix ? 'pl-11' : ''} ${showTerminalPrefix ? 'pl-8' : ''} ${className || ''}`,
            })}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            {...props}
          />
          <AnimatePresence>
            {isFocused && (
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                exit={{ scaleX: 0 }}
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-quantum-500 to-quantum-400 origin-left"
              />
            )}
          </AnimatePresence>
        </div>
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-sm text-red-400"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Input.displayName = 'Input';

// Textarea Component
export interface TextareaProps
  extends TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof inputVariants> {
  label?: string;
  error?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant, inputSize, label, error, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-zinc-400">{label}</label>
        )}
        <textarea
          ref={ref}
          className={inputVariants({
            variant: error ? 'error' : variant,
            inputSize,
            className: `min-h-[100px] resize-y ${className || ''}`,
          })}
          {...props}
        />
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-sm text-red-400"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { Input, Textarea, inputVariants };
