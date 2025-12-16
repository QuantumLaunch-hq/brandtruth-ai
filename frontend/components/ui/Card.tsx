'use client';

import { forwardRef, HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, HTMLMotionProps } from 'framer-motion';

const cardVariants = cva(
  'rounded-xl overflow-hidden transition-all duration-300',
  {
    variants: {
      variant: {
        default: 'bg-zinc-900/80 border border-zinc-800 hover:border-zinc-700',
        elevated: 'bg-zinc-900 border border-zinc-800 shadow-xl shadow-black/20',
        glow: 'bg-zinc-900/80 border border-quantum-500/30 shadow-lg shadow-quantum-500/10 hover:shadow-quantum-500/20 hover:border-quantum-500/50',
        glass: 'bg-zinc-900/50 backdrop-blur-xl border border-zinc-700/50',
        interactive: 'bg-zinc-900/80 border border-zinc-800 hover:border-quantum-500/30 hover:shadow-lg hover:shadow-quantum-500/5 cursor-pointer',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'md',
    },
  }
);

export interface CardProps
  extends Omit<HTMLMotionProps<'div'>, 'children'>,
    VariantProps<typeof cardVariants> {
  animate?: boolean;
  children?: React.ReactNode;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, animate = false, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cardVariants({ variant, padding, className })}
        initial={animate ? { opacity: 0, y: 20 } : false}
        animate={animate ? { opacity: 1, y: 0 } : false}
        transition={animate ? { duration: 0.3 } : undefined}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex flex-col space-y-1.5 ${className || ''}`}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

// Card Title Component
const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={`text-lg font-semibold text-white ${className || ''}`}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

// Card Description Component
const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={`text-sm text-zinc-400 ${className || ''}`}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

// Card Content Component
const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={className || ''} {...props} />
  )
);
CardContent.displayName = 'CardContent';

// Card Footer Component
const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex items-center pt-4 ${className || ''}`}
      {...props}
    />
  )
);
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, cardVariants };
