import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// POST /api/variants/[id]/approve - Approve a variant
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Update variant to APPROVED
    const variant = await prisma.variant.update({
      where: { id: params.id },
      data: {
        status: 'APPROVED',
        updatedAt: new Date(),
      },
      include: {
        campaign: {
          select: {
            id: true,
            name: true,
            status: true,
          },
        },
      },
    });

    // Count variants by status
    const [pendingCount, approvedCount, rejectedCount] = await Promise.all([
      prisma.variant.count({
        where: { campaignId: variant.campaignId, status: 'PENDING' },
      }),
      prisma.variant.count({
        where: { campaignId: variant.campaignId, status: 'APPROVED' },
      }),
      prisma.variant.count({
        where: { campaignId: variant.campaignId, status: 'REJECTED' },
      }),
    ]);

    // Update campaign status if all variants reviewed and at least one approved
    if (pendingCount === 0 && approvedCount > 0) {
      await prisma.campaign.update({
        where: { id: variant.campaignId },
        data: { status: 'APPROVED' },
      });
    }

    return NextResponse.json({
      success: true,
      variant: {
        id: variant.id,
        headline: variant.headline,
        status: variant.status,
      },
      campaign: {
        id: variant.campaignId,
        pendingCount,
        approvedCount,
        rejectedCount,
        allReviewed: pendingCount === 0,
        readyToPublish: pendingCount === 0 && approvedCount > 0,
      },
    });
  } catch (error) {
    console.error('Error approving variant:', error);

    if ((error as any)?.code === 'P2025') {
      return NextResponse.json(
        { error: 'Variant not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to approve variant' },
      { status: 500 }
    );
  }
}
