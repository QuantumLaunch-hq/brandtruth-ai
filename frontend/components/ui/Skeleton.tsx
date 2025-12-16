'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { motion } from 'framer-motion';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'circular' | 'text' | 'card';
  width?: string | number;
  height?: string | number;
  count?: number;
}

const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = 'default', width, height, count = 1, className, ...props }, ref) => {
    const baseClasses = 'bg-zinc-800 animate-pulse';

    const variantClasses = {
      default: 'rounded-lg',
      circular: 'rounded-full',
      text: 'rounded h-4',
      card: 'rounded-xl',
    };

    const skeletons = Array.from({ length: count }, (_, i) => (
      <div
        key={i}
        className={`${baseClasses} ${variantClasses[variant]} ${className || ''}`}
        style={{
          width: width || '100%',
          height: variant === 'text' ? 16 : height || (variant === 'circular' ? width : 40),
        }}
        {...props}
      />
    ));

    if (count === 1) {
      return (
        <div
          ref={ref}
          className={`${baseClasses} ${variantClasses[variant]} ${className || ''}`}
          style={{
            width: width || '100%',
            height: variant === 'text' ? 16 : height || (variant === 'circular' ? width : 40),
          }}
          {...props}
        />
      );
    }

    return (
      <div ref={ref} className="space-y-2">
        {skeletons}
      </div>
    );
  }
);

Skeleton.displayName = 'Skeleton';

// Skeleton Card - Pre-built skeleton for card layouts
const SkeletonCard = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`bg-zinc-900 border border-zinc-800 rounded-xl p-6 ${className || ''}`}
        {...props}
      >
        <div className="flex items-start gap-4">
          <Skeleton variant="circular" width={48} height={48} />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width="40%" />
          </div>
        </div>
        <div className="mt-4 space-y-2">
          <Skeleton variant="text" />
          <Skeleton variant="text" width="80%" />
        </div>
      </div>
    );
  }
);

SkeletonCard.displayName = 'SkeletonCard';

// Skeleton List - Pre-built skeleton for list layouts
interface SkeletonListProps extends HTMLAttributes<HTMLDivElement> {
  count?: number;
  showAvatar?: boolean;
}

const SkeletonList = forwardRef<HTMLDivElement, SkeletonListProps>(
  ({ count = 3, showAvatar = true, className, ...props }, ref) => {
    return (
      <div ref={ref} className={`space-y-4 ${className || ''}`} {...props}>
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className="flex items-center gap-4">
            {showAvatar && <Skeleton variant="circular" width={40} height={40} />}
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="70%" />
              <Skeleton variant="text" width="50%" />
            </div>
          </div>
        ))}
      </div>
    );
  }
);

SkeletonList.displayName = 'SkeletonList';

// Shimmer Effect - Animated loading overlay
interface ShimmerProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
}

const Shimmer = forwardRef<HTMLDivElement, ShimmerProps>(
  ({ width = '100%', height = 200, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`relative overflow-hidden bg-zinc-900 rounded-xl ${className || ''}`}
        style={{ width, height }}
        {...props}
      >
        <motion.div
          className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-zinc-700/30 to-transparent"
          animate={{ translateX: ['−100%', '100%'] }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      </div>
    );
  }
);

Shimmer.displayName = 'Shimmer';

// Loading Spinner with Quantum style
interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

const Spinner = forwardRef<HTMLDivElement, SpinnerProps>(
  ({ size = 'md', label, className, ...props }, ref) => {
    const sizeClasses = {
      sm: 'w-4 h-4',
      md: 'w-8 h-8',
      lg: 'w-12 h-12',
    };

    return (
      <div
        ref={ref}
        className={`flex flex-col items-center justify-center gap-3 ${className || ''}`}
        {...props}
      >
        <motion.div
          className={`${sizeClasses[size]} border-2 border-zinc-700 border-t-quantum-500 rounded-full`}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
        {label && (
          <motion.span
            className="text-sm text-zinc-400"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            {label}
          </motion.span>
        )}
      </div>
    );
  }
);

Spinner.displayName = 'Spinner';

// Orbital Loader - Quantum-style AI processing animation
interface OrbitalLoaderProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

const OrbitalLoader = forwardRef<HTMLDivElement, OrbitalLoaderProps>(
  ({ size = 'md', text, className, ...props }, ref) => {
    const sizeConfig = {
      sm: { container: 'w-16 h-16', dot: 'w-2 h-2', orbit: 6 },
      md: { container: 'w-24 h-24', dot: 'w-3 h-3', orbit: 9 },
      lg: { container: 'w-32 h-32', dot: 'w-4 h-4', orbit: 12 },
    };

    const config = sizeConfig[size];

    return (
      <div
        ref={ref}
        className={`flex flex-col items-center gap-4 ${className || ''}`}
        {...props}
      >
        <div className={`relative ${config.container}`}>
          {/* Center glow */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              className="w-4 h-4 bg-quantum-500 rounded-full"
              animate={{
                boxShadow: [
                  '0 0 20px rgba(34, 197, 94, 0.5)',
                  '0 0 40px rgba(34, 197, 94, 0.8)',
                  '0 0 20px rgba(34, 197, 94, 0.5)',
                ],
              }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          {/* Orbiting dots */}
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-0"
              animate={{ rotate: 360 }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'linear',
                delay: i * 0.5,
              }}
            >
              <div
                className={`${config.dot} bg-quantum-400 rounded-full absolute`}
                style={{
                  top: config.orbit,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  opacity: 1 - i * 0.25,
                }}
              />
            </motion.div>
          ))}
        </div>
        {text && (
          <motion.span
            className="text-sm text-zinc-400"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            {text}
          </motion.span>
        )}
      </div>
    );
  }
);

OrbitalLoader.displayName = 'OrbitalLoader';

export { Skeleton, SkeletonCard, SkeletonList, Shimmer, Spinner, OrbitalLoader };
