'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-zinc-800 text-zinc-300 border border-zinc-700',
        quantum: 'bg-quantum-500/10 text-quantum-400 border border-quantum-500/20',
        success: 'bg-green-500/10 text-green-400 border border-green-500/20',
        warning: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
        danger: 'bg-red-500/10 text-red-400 border border-red-500/20',
        info: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
        purple: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
        outline: 'bg-transparent border border-zinc-600 text-zinc-400',
      },
      size: {
        sm: 'text-xs px-2 py-0.5 rounded',
        md: 'text-sm px-2.5 py-1 rounded-md',
        lg: 'text-sm px-3 py-1.5 rounded-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, icon, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={badgeVariants({ variant, size, className })}
        {...props}
      >
        {icon && <span className="mr-1.5">{icon}</span>}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// Score Badge - specialized for scores
interface ScoreBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const ScoreBadge = forwardRef<HTMLSpanElement, ScoreBadgeProps>(
  ({ score, size = 'md', showLabel = false, className, ...props }, ref) => {
    const getVariant = (score: number) => {
      if (score >= 80) return 'success';
      if (score >= 60) return 'warning';
      return 'danger';
    };

    const getLabel = (score: number) => {
      if (score >= 90) return 'Excellent';
      if (score >= 80) return 'Good';
      if (score >= 60) return 'Fair';
      return 'Poor';
    };

    return (
      <Badge
        ref={ref}
        variant={getVariant(score)}
        size={size}
        className={`font-mono ${className || ''}`}
        {...props}
      >
        {score}
        {showLabel && <span className="ml-1.5 font-sans">{getLabel(score)}</span>}
      </Badge>
    );
  }
);

ScoreBadge.displayName = 'ScoreBadge';

// Risk Badge - specialized for risk levels
interface RiskBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  level: 'low' | 'medium' | 'high';
  size?: 'sm' | 'md' | 'lg';
}

const RiskBadge = forwardRef<HTMLSpanElement, RiskBadgeProps>(
  ({ level, size = 'md', className, ...props }, ref) => {
    const variantMap = {
      low: 'success',
      medium: 'warning',
      high: 'danger',
    } as const;

    const labelMap = {
      low: 'Low Risk',
      medium: 'Medium Risk',
      high: 'High Risk',
    };

    return (
      <Badge
        ref={ref}
        variant={variantMap[level]}
        size={size}
        className={className}
        {...props}
      >
        {labelMap[level]}
      </Badge>
    );
  }
);

RiskBadge.displayName = 'RiskBadge';

// Status Badge - for online/offline/loading states
interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: 'online' | 'offline' | 'loading' | 'error';
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ status, size = 'md', showDot = true, className, children, ...props }, ref) => {
    const variantMap = {
      online: 'success',
      offline: 'default',
      loading: 'info',
      error: 'danger',
    } as const;

    const labelMap = {
      online: 'Online',
      offline: 'Offline',
      loading: 'Loading',
      error: 'Error',
    };

    return (
      <Badge
        ref={ref}
        variant={variantMap[status]}
        size={size}
        className={className}
        {...props}
      >
        {showDot && (
          <span
            className={`w-2 h-2 rounded-full mr-2 ${
              status === 'online'
                ? 'bg-green-400 animate-pulse'
                : status === 'loading'
                ? 'bg-blue-400 animate-pulse'
                : status === 'error'
                ? 'bg-red-400'
                : 'bg-zinc-500'
            }`}
          />
        )}
        {children || labelMap[status]}
      </Badge>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';

export { Badge, ScoreBadge, RiskBadge, StatusBadge, badgeVariants };
