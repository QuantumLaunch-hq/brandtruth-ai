'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  Plus,
  Search,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  MoreHorizontal,
  ArrowRight,
  Globe,
  Image as ImageIcon,
  BarChart3,
  User,
  LogOut,
  ChevronDown
} from 'lucide-react';

// Campaign status badge component
const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig: Record<string, { color: string; icon: typeof CheckCircle; label: string }> = {
    DRAFT: { color: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20', icon: Clock, label: 'Draft' },
    PROCESSING: { color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', icon: Loader2, label: 'Processing' },
    READY: { color: 'bg-blue-500/10 text-blue-400 border-blue-500/20', icon: CheckCircle, label: 'Ready' },
    APPROVED: { color: 'bg-quantum-500/10 text-quantum-400 border-quantum-500/20', icon: CheckCircle, label: 'Approved' },
    PUBLISHED: { color: 'bg-purple-500/10 text-purple-400 border-purple-500/20', icon: ExternalLink, label: 'Published' },
    FAILED: { color: 'bg-red-500/10 text-red-400 border-red-500/20', icon: XCircle, label: 'Failed' },
    CANCELLED: { color: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20', icon: XCircle, label: 'Cancelled' },
  };

  const config = statusConfig[status] || statusConfig.DRAFT;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border ${config.color}`}>
      <Icon className={`w-3.5 h-3.5 ${status === 'PROCESSING' ? 'animate-spin' : ''}`} />
      {config.label}
    </span>
  );
};

// Campaign type from API
interface Campaign {
  id: string;
  name: string;
  url: string;
  status: string;
  variantCount: number;
  approvedCount: number;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
  workflowId: string | null;
}

export default function CampaignsPage() {
  const { data: session, status } = useSession();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch campaigns from API
  useEffect(() => {
    const fetchCampaigns = async () => {
      // Fetch regardless of auth status (API handles auth internally)
      // Skip only during initial loading state
      if (status === 'loading') {
        return;
      }

      try {
        const response = await fetch('/api/campaigns');
        if (!response.ok) {
          throw new Error('Failed to fetch campaigns');
        }
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      } catch (err) {
        console.error('Failed to fetch campaigns:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch campaigns');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCampaigns();
    // Refresh every 10 seconds to catch processing updates
    const interval = setInterval(fetchCampaigns, 10000);
    return () => clearInterval(interval);
  }, [status]);

  // Format relative time
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Filter campaigns
  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         campaign.url.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = !filterStatus || campaign.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  if (status === 'loading' || isLoading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-quantum-500 animate-spin mx-auto mb-4" />
          <p className="text-zinc-400 text-sm">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Failed to load campaigns</h2>
          <p className="text-zinc-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-quantum-500 text-white rounded-lg hover:bg-quantum-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-zinc-900/50 border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 text-white">
              <Zap className="w-7 h-7 text-quantum-500" />
              <span className="text-lg font-bold">QuantumLaunch</span>
            </Link>

            {/* Nav */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/campaigns" className="text-white font-medium border-b-2 border-quantum-500 pb-0.5">
                Campaigns
              </Link>
              <Link href="/tools" className="text-zinc-400 hover:text-white transition-colors">
                Tools
              </Link>
            </nav>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-quantum-500 to-purple-500 flex items-center justify-center text-white text-sm font-medium">
                  {session?.user?.name?.[0]?.toUpperCase() || session?.user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <span className="hidden sm:block text-sm text-zinc-300">
                  {session?.user?.name || session?.user?.email?.split('@')[0]}
                </span>
                <ChevronDown className="w-4 h-4 text-zinc-500" />
              </button>

              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl overflow-hidden"
                  >
                    <div className="p-3 border-b border-zinc-800">
                      <p className="text-sm font-medium text-white">{session?.user?.name}</p>
                      <p className="text-xs text-zinc-500">{session?.user?.email}</p>
                    </div>
                    <div className="p-1">
                      <button
                        onClick={() => signOut({ callbackUrl: '/' })}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign out
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Campaigns</h1>
            <p className="text-zinc-400 mt-1">Manage your ad campaigns</p>
          </div>
          <Link href="/studio">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-quantum-500 to-quantum-600 text-white font-semibold rounded-lg shadow-lg shadow-quantum-500/25 hover:shadow-quantum-500/40 transition-all"
            >
              <Plus className="w-5 h-5" />
              New Campaign
            </motion.button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-2.5 bg-zinc-900/80 border border-zinc-800 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500 transition-colors"
            />
          </div>

          {/* Status filter */}
          <div className="flex gap-2">
            {['All', 'PROCESSING', 'READY', 'PUBLISHED'].map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status === 'All' ? null : status)}
                className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  (status === 'All' && !filterStatus) || filterStatus === status
                    ? 'bg-quantum-500/20 text-quantum-400 border border-quantum-500/30'
                    : 'bg-zinc-900/80 text-zinc-400 border border-zinc-800 hover:bg-zinc-800'
                }`}
              >
                {status === 'All' ? 'All' : status.charAt(0) + status.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Campaigns grid */}
        {filteredCampaigns.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-900 flex items-center justify-center">
              <Search className="w-8 h-8 text-zinc-600" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No campaigns found</h3>
            <p className="text-zinc-500 mb-6">
              {searchQuery ? 'Try adjusting your search or filters' : 'Create your first campaign to get started'}
            </p>
            {!searchQuery && (
              <Link href="/studio">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-quantum-500 to-quantum-600 text-white font-semibold rounded-lg shadow-lg shadow-quantum-500/25"
                >
                  <Plus className="w-5 h-5" />
                  New Campaign
                </motion.button>
              </Link>
            )}
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-4"
          >
            {filteredCampaigns.map((campaign) => (
              <motion.div
                key={campaign.id}
                variants={itemVariants}
                whileHover={{ scale: 1.01 }}
                className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-all group cursor-pointer"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white truncate">
                        {campaign.name}
                      </h3>
                      <StatusBadge status={campaign.status} />
                    </div>
                    <div className="flex items-center gap-4 text-sm text-zinc-500">
                      <span className="flex items-center gap-1.5">
                        <Globe className="w-4 h-4" />
                        {new URL(campaign.url).hostname}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <ImageIcon className="w-4 h-4" />
                        {campaign.variantCount} variants
                      </span>
                      {campaign.approvedCount > 0 && (
                        <span className="flex items-center gap-1.5 text-quantum-400">
                          <CheckCircle className="w-4 h-4" />
                          {campaign.approvedCount} approved
                        </span>
                      )}
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        {formatRelativeTime(campaign.updatedAt)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <BarChart3 className="w-5 h-5" />
                    </motion.button>
                    <Link href={`/campaigns/${campaign.id}`}>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-quantum-500/10 text-quantum-400 font-medium hover:bg-quantum-500/20 transition-colors"
                      >
                        Open
                        <ArrowRight className="w-4 h-4" />
                      </motion.button>
                    </Link>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Info notice when no campaigns */}
        {campaigns.length === 0 && !searchQuery && !filterStatus && (
          <div className="mt-8 p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
            <p className="text-sm text-zinc-500">
              <span className="text-quantum-400 font-medium">Tip:</span> Create your first campaign from Studio.
              Campaigns are automatically saved when you run the pipeline.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
