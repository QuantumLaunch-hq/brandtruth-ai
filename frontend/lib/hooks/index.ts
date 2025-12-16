// lib/hooks/index.ts
// Re-export all custom hooks

export {
  useWorkflowProgress,
  getStageLabel,
  isTerminalStage,
  type WorkflowProgress,
  type WorkflowStage,
  type UseWorkflowProgressOptions,
  type UseWorkflowProgressReturn,
} from './useWorkflowProgress';

export {
  useWorkflow,
  type WorkflowConfig,
  type WorkflowResult,
  type BrandProfile,
  type CopyVariant,
  type PerformanceScore,
  type UseWorkflowReturn,
} from './useWorkflow';

export {
  useUser,
  type User,
} from './useUser';
