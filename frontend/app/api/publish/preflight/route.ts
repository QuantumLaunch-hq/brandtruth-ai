import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

interface PreflightCheck {
  id: string;
  name: string;
  status: 'pass' | 'fail' | 'warning';
  message: string;
  required: boolean;
}

// POST /api/publish/preflight - Run pre-flight checks before publishing
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { campaignId } = body;

    if (!campaignId) {
      return NextResponse.json(
        { error: 'campaignId is required' },
        { status: 400 }
      );
    }

    // Fetch campaign with variants
    const campaign = await prisma.campaign.findUnique({
      where: { id: campaignId },
      include: {
        variants: true,
        user: {
          select: {
            id: true,
            email: true,
          },
        },
      },
    });

    if (!campaign) {
      return NextResponse.json(
        { error: 'Campaign not found' },
        { status: 404 }
      );
    }

    const checks: PreflightCheck[] = [];

    // Check 1: Has approved variants
    const approvedVariants = campaign.variants.filter(v => v.status === 'APPROVED');
    checks.push({
      id: 'approved_variants',
      name: 'Approved Variants',
      status: approvedVariants.length > 0 ? 'pass' : 'fail',
      message: approvedVariants.length > 0
        ? `${approvedVariants.length} variant(s) approved`
        : 'No approved variants. Approve at least one variant to publish.',
      required: true,
    });

    // Check 2: All approved variants have images
    const variantsWithImages = approvedVariants.filter(v => v.composedUrl || v.imageUrl);
    checks.push({
      id: 'variant_images',
      name: 'Variant Images',
      status: variantsWithImages.length === approvedVariants.length ? 'pass' : 'warning',
      message: variantsWithImages.length === approvedVariants.length
        ? 'All approved variants have images'
        : `${approvedVariants.length - variantsWithImages.length} variant(s) missing images`,
      required: false,
    });

    // Check 3: Meta API configured
    const metaAccessToken = process.env.META_ACCESS_TOKEN;
    const metaAdAccountId = process.env.META_AD_ACCOUNT_ID;
    const metaConfigured = !!(metaAccessToken && metaAdAccountId);
    checks.push({
      id: 'meta_api',
      name: 'Meta API Connected',
      status: metaConfigured ? 'pass' : 'fail',
      message: metaConfigured
        ? 'Meta API credentials configured'
        : 'Meta API not configured. Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID.',
      required: true,
    });

    // Check 4: Budget configured
    const budgetResult = campaign.budgetResult as any;
    const hasBudget = budgetResult && budgetResult.daily_budget > 0;
    checks.push({
      id: 'budget',
      name: 'Budget Set',
      status: hasBudget ? 'pass' : 'warning',
      message: hasBudget
        ? `Daily budget: $${budgetResult.daily_budget}`
        : 'No budget configured. Default will be used.',
      required: false,
    });

    // Check 5: Campaign not already published
    const alreadyPublished = campaign.status === 'PUBLISHED';
    checks.push({
      id: 'not_published',
      name: 'Not Already Published',
      status: alreadyPublished ? 'warning' : 'pass',
      message: alreadyPublished
        ? 'Campaign already published. Publishing again will create duplicates.'
        : 'Campaign ready for first publish',
      required: false,
    });

    // Check 6: Destination URL set
    const hasDestinationUrl = !!campaign.url;
    checks.push({
      id: 'destination_url',
      name: 'Destination URL',
      status: hasDestinationUrl ? 'pass' : 'fail',
      message: hasDestinationUrl
        ? `Click-through URL: ${campaign.url}`
        : 'No destination URL set for ad clicks.',
      required: true,
    });

    // Calculate overall status
    const failedRequired = checks.filter(c => c.required && c.status === 'fail');
    const warnings = checks.filter(c => c.status === 'warning');

    const canPublish = failedRequired.length === 0;
    const overallStatus = failedRequired.length > 0
      ? 'blocked'
      : warnings.length > 0
        ? 'ready_with_warnings'
        : 'ready';

    return NextResponse.json({
      campaignId,
      campaignName: campaign.name,
      canPublish,
      status: overallStatus,
      checks,
      summary: {
        total: checks.length,
        passed: checks.filter(c => c.status === 'pass').length,
        warnings: warnings.length,
        failed: failedRequired.length,
      },
      approvedVariants: approvedVariants.map(v => ({
        id: v.id,
        headline: v.headline,
        imageUrl: v.composedUrl || v.imageUrl,
      })),
    });
  } catch (error) {
    console.error('Error running preflight checks:', error);
    return NextResponse.json(
      { error: 'Failed to run preflight checks' },
      { status: 500 }
    );
  }
}
