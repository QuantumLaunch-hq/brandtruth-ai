'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  Download,
  Share2,
  MoreHorizontal,
  Sparkles,
} from 'lucide-react';

interface Variant {
  id: string;
  headline: string;
  primaryText: string;
  cta: string;
  angle?: string;
  emotion?: string;
  imageUrl?: string;
  composedUrl?: string;
  score?: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}

interface Campaign {
  id: string;
  name: string;
  url: string;
  status: string;
  workflowId?: string;
  brandProfile?: {
    brand_name?: string;
    tagline?: string;
    industry?: string;
    confidence_score?: number;
  };
  variants: Variant[];
  createdAt: string;
  updatedAt: string;
}

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);

  // Fetch campaign details
  useEffect(() => {
    const fetchCampaign = async () => {
      try {
        const response = await fetch(`/api/campaigns/${campaignId}`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Campaign not found');
          }
          throw new Error('Failed to fetch campaign');
        }
        const data = await response.json();
        setCampaign(data.campaign);
      } catch (err) {
        console.error('Failed to fetch campaign:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch campaign');
      } finally {
        setIsLoading(false);
      }
    };

    if (campaignId) {
      fetchCampaign();
    }
  }, [campaignId]);

  // Handle variant approval
  const handleApprove = async (variantId: string) => {
    try {
      const response = await fetch(`/api/variants/${variantId}/approve`, {
        method: 'POST',
      });
      if (response.ok) {
        setCampaign(prev => prev ? {
          ...prev,
          variants: prev.variants.map(v =>
            v.id === variantId ? { ...v, status: 'APPROVED' as const } : v
          ),
        } : null);
      }
    } catch (err) {
      console.error('Failed to approve variant:', err);
    }
  };

  // Handle variant rejection
  const handleReject = async (variantId: string) => {
    try {
      const response = await fetch(`/api/variants/${variantId}/reject`, {
        method: 'POST',
      });
      if (response.ok) {
        setCampaign(prev => prev ? {
          ...prev,
          variants: prev.variants.map(v =>
            v.id === variantId ? { ...v, status: 'REJECTED' as const } : v
          ),
        } : null);
      }
    } catch (err) {
      console.error('Failed to reject variant:', err);
    }
  };

  // Get image URL with fallback
  const getImageUrl = (variant: Variant) => {
    const url = variant.composedUrl || variant.imageUrl;
    if (!url) return 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010'}${url}`;
  };

  // Status badge component
  const StatusBadge = ({ status }: { status: string }) => {
    const styles: Record<string, string> = {
      PENDING: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      APPROVED: 'bg-green-500/20 text-green-400 border-green-500/30',
      REJECTED: 'bg-red-500/20 text-red-400 border-red-500/30',
      READY: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      PUBLISHED: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${styles[status] || styles.PENDING}`}>
        {status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{error || 'Campaign not found'}</p>
        <Link href="/campaigns" className="text-orange-400 hover:text-orange-300">
          Back to Campaigns
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/campaigns')}
                className="p-2 hover:bg-zinc-800 rounded-lg transition"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-semibold">{campaign.name}</h1>
                <div className="flex items-center gap-2 mt-1">
                  <a
                    href={campaign.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-zinc-400 hover:text-orange-400 flex items-center gap-1"
                  >
                    {campaign.url}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                  <StatusBadge status={campaign.status} />
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export
              </button>
              <button className="px-4 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg text-sm font-medium transition flex items-center gap-2">
                <Share2 className="w-4 h-4" />
                Publish
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Brand Info */}
        {campaign.brandProfile && (
          <div className="mb-8 p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-orange-400" />
              Brand Profile
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-zinc-500 mb-1">Brand Name</p>
                <p className="font-medium">{campaign.brandProfile.brand_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Industry</p>
                <p className="font-medium">{campaign.brandProfile.industry || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Tagline</p>
                <p className="font-medium">{campaign.brandProfile.tagline || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Confidence</p>
                <p className="font-medium">{campaign.brandProfile.confidence_score ? `${Math.round(campaign.brandProfile.confidence_score * 100)}%` : 'N/A'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Variants Grid */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            Ad Variants ({campaign.variants.length})
          </h2>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-green-400">
              {campaign.variants.filter(v => v.status === 'APPROVED').length} approved
            </span>
            <span className="text-yellow-400">
              {campaign.variants.filter(v => v.status === 'PENDING').length} pending
            </span>
            <span className="text-red-400">
              {campaign.variants.filter(v => v.status === 'REJECTED').length} rejected
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaign.variants.map((variant) => (
            <motion.div
              key={variant.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`bg-zinc-900/50 border rounded-xl overflow-hidden ${
                variant.status === 'APPROVED'
                  ? 'border-green-500/30'
                  : variant.status === 'REJECTED'
                  ? 'border-red-500/30'
                  : 'border-zinc-800'
              }`}
            >
              {/* Image */}
              <div
                className="relative aspect-square bg-zinc-800 cursor-pointer"
                onClick={() => setSelectedVariant(variant)}
              >
                <Image
                  src={getImageUrl(variant)}
                  alt={variant.headline}
                  fill
                  className="object-cover"
                  unoptimized={getImageUrl(variant).includes('localhost')}
                />
                {variant.score && (
                  <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs font-medium">
                    Score: {variant.score}
                  </div>
                )}
                <StatusBadge status={variant.status} />
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-sm mb-2 line-clamp-2">{variant.headline}</h3>
                <p className="text-xs text-zinc-400 mb-3 line-clamp-2">{variant.primaryText}</p>

                <div className="flex items-center gap-2 mb-4">
                  {variant.angle && (
                    <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs">{variant.angle}</span>
                  )}
                  {variant.emotion && (
                    <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs">{variant.emotion}</span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {variant.status === 'PENDING' ? (
                    <>
                      <button
                        onClick={() => handleApprove(variant.id)}
                        className="flex-1 px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-xs font-medium transition flex items-center justify-center gap-1"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(variant.id)}
                        className="flex-1 px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs font-medium transition flex items-center justify-center gap-1"
                      >
                        <XCircle className="w-3 h-3" />
                        Reject
                      </button>
                    </>
                  ) : (
                    <div className="flex-1 text-center text-xs text-zinc-500">
                      {variant.status === 'APPROVED' ? 'Approved' : 'Rejected'}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </main>

      {/* Variant Detail Modal */}
      {selectedVariant && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6"
          onClick={() => setSelectedVariant(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-zinc-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="grid md:grid-cols-2">
              <div className="relative aspect-square bg-zinc-800">
                <Image
                  src={getImageUrl(selectedVariant)}
                  alt={selectedVariant.headline}
                  fill
                  className="object-cover"
                  unoptimized={getImageUrl(selectedVariant).includes('localhost')}
                />
              </div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <StatusBadge status={selectedVariant.status} />
                  {selectedVariant.score && (
                    <span className="text-sm text-zinc-400">Score: {selectedVariant.score}</span>
                  )}
                </div>
                <h2 className="text-xl font-semibold mb-4">{selectedVariant.headline}</h2>
                <p className="text-zinc-400 mb-6">{selectedVariant.primaryText}</p>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Call to Action</p>
                    <p className="font-medium">{selectedVariant.cta}</p>
                  </div>
                  {selectedVariant.angle && (
                    <div>
                      <p className="text-xs text-zinc-500 mb-1">Angle</p>
                      <p className="font-medium">{selectedVariant.angle}</p>
                    </div>
                  )}
                  {selectedVariant.emotion && (
                    <div>
                      <p className="text-xs text-zinc-500 mb-1">Emotion</p>
                      <p className="font-medium">{selectedVariant.emotion}</p>
                    </div>
                  )}
                </div>
                <div className="mt-6 pt-6 border-t border-zinc-800 flex gap-2">
                  {selectedVariant.status === 'PENDING' && (
                    <>
                      <button
                        onClick={() => {
                          handleApprove(selectedVariant.id);
                          setSelectedVariant({ ...selectedVariant, status: 'APPROVED' });
                        }}
                        className="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg font-medium transition"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => {
                          handleReject(selectedVariant.id);
                          setSelectedVariant({ ...selectedVariant, status: 'REJECTED' });
                        }}
                        className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg font-medium transition"
                      >
                        Reject
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setSelectedVariant(null)}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
