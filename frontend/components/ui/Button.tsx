'use client';

import { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, HTMLMotionProps } from 'framer-motion';

const buttonVariants = cva(
  'inline-flex items-center justify-center font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-quantum-500/50',
  {
    variants: {
      variant: {
        primary: 'bg-gradient-to-r from-quantum-500 to-quantum-600 text-black shadow-lg shadow-quantum-500/25 hover:shadow-quantum-500/40 hover:from-quantum-400 hover:to-quantum-500 active:scale-[0.98]',
        secondary: 'bg-transparent border border-zinc-700 text-white hover:border-quantum-500/50 hover:bg-quantum-500/5 active:scale-[0.98]',
        ghost: 'bg-transparent text-zinc-400 hover:text-white hover:bg-zinc-800/50',
        danger: 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg shadow-red-500/25 hover:shadow-red-500/40 active:scale-[0.98]',
      },
      size: {
        sm: 'text-sm px-3 py-1.5 rounded-lg gap-1.5',
        md: 'text-sm px-4 py-2.5 rounded-lg gap-2',
        lg: 'text-base px-6 py-3 rounded-xl gap-2',
        xl: 'text-lg px-8 py-4 rounded-xl gap-3',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends Omit<HTMLMotionProps<'button'>, 'children'>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, icon, children, disabled, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        className={buttonVariants({ variant, size, className })}
        disabled={disabled || loading}
        whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
        {...props}
      >
        {loading ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : icon ? (
          icon
        ) : null}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
