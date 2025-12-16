'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Command {
  id: string;
  icon: string;
  label: string;
  description: string;
  shortcut?: string;
  action: () => void;
}

export default function CommandPalette({ 
  isOpen, 
  onClose, 
  onCommand 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  onCommand: (command: string) => void;
}) {
  const [search, setSearch] = useState('');
  
  const commands: Command[] = [
    { id: 'hooks', icon: '🪝', label: 'Generate Hooks', description: 'Create scroll-stopping ad headlines', shortcut: '⌘H', action: () => onCommand('Generate hooks for my product') },
    { id: 'campaign', icon: '🚀', label: 'New Campaign', description: 'Start a full campaign from scratch', shortcut: '⌘N', action: () => onCommand('Create a new campaign') },
    { id: 'budget', icon: '💰', label: 'Plan Budget', description: 'Calculate optimal ad spend', shortcut: '⌘B', action: () => onCommand('Help me plan my budget') },
    { id: 'audience', icon: '👥', label: 'Find Audience', description: 'Discover your ideal customers', shortcut: '⌘A', action: () => onCommand('Find my target audience') },
    { id: 'analyze', icon: '📊', label: 'Analyze Performance', description: 'Check how your ads are doing', shortcut: '⌘P', action: () => onCommand('Analyze my ad performance') },
    { id: 'competitor', icon: '🕵️', label: 'Spy on Competitors', description: 'See what competitors are running', shortcut: '⌘C', action: () => onCommand('Show me competitor ads') },
    { id: 'abtest', icon: '🧪', label: 'Plan A/B Test', description: 'Design statistically valid tests', shortcut: '⌘T', action: () => onCommand('Help me plan an A/B test') },
    { id: 'export', icon: '📦', label: 'Export Assets', description: 'Download all ad sizes', shortcut: '⌘E', action: () => onCommand('Export my ads') },
    { id: 'landing', icon: '🔍', label: 'Check Landing Page', description: 'Verify message match', shortcut: '⌘L', action: () => onCommand('Analyze my landing page') },
    { id: 'iterate', icon: '🔄', label: 'Fix Underperforming Ads', description: 'Get improvement suggestions', shortcut: '⌘I', action: () => onCommand('Help me fix my underperforming ads') },
  ];
  
  const filteredCommands = commands.filter(cmd => 
    cmd.label.toLowerCase().includes(search.toLowerCase()) ||
    cmd.description.toLowerCase().includes(search.toLowerCase())
  );
  
  const handleSelect = (command: Command) => {
    command.action();
    onClose();
    setSearch('');
  };
  
  // Keyboard navigation
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  useEffect(() => {
    if (!isOpen) {
      setSearch('');
      setSelectedIndex(0);
    }
  }, [isOpen]);
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
      } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        handleSelect(filteredCommands[selectedIndex]);
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);
  
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
          
          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
          >
            <div className="bg-[#1a1a24] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
              {/* Search input */}
              <div className="p-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setSelectedIndex(0); }}
                    placeholder="What do you want to do?"
                    className="flex-1 bg-transparent text-white text-lg outline-none placeholder:text-white/30"
                    autoFocus
                  />
                  <kbd className="px-2 py-1 bg-white/10 rounded text-xs text-white/50">ESC</kbd>
                </div>
              </div>
              
              {/* Commands list */}
              <div className="max-h-[400px] overflow-y-auto p-2">
                {filteredCommands.length === 0 ? (
                  <div className="p-8 text-center text-white/30">
                    No commands found
                  </div>
                ) : (
                  filteredCommands.map((command, i) => (
                    <button
                      key={command.id}
                      onClick={() => handleSelect(command)}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={`w-full flex items-center gap-4 p-3 rounded-xl transition ${
                        i === selectedIndex ? 'bg-violet-600/30' : 'hover:bg-white/5'
                      }`}
                    >
                      <span className="text-2xl">{command.icon}</span>
                      <div className="flex-1 text-left">
                        <div className="font-medium text-white">{command.label}</div>
                        <div className="text-sm text-white/50">{command.description}</div>
                      </div>
                      {command.shortcut && (
                        <kbd className="px-2 py-1 bg-white/10 rounded text-xs text-white/50">{command.shortcut}</kbd>
                      )}
                    </button>
                  ))
                )}
              </div>
              
              {/* Footer hint */}
              <div className="p-3 border-t border-white/10 flex items-center justify-between text-xs text-white/30">
                <div className="flex gap-4">
                  <span>↑↓ Navigate</span>
                  <span>↵ Select</span>
                </div>
                <span>Type anything to search</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
