import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// POST /api/variants/[id]/reject - Reject a variant
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Optionally get rejection reason from body
    let reason: string | undefined;
    try {
      const body = await request.json();
      reason = body.reason;
    } catch {
      // No body is fine
    }

    // Update variant to REJECTED
    const variant = await prisma.variant.update({
      where: { id: params.id },
      data: {
        status: 'REJECTED',
        updatedAt: new Date(),
        // Store rejection reason in scoreDetails if provided
        ...(reason && {
          scoreDetails: {
            rejectionReason: reason,
            rejectedAt: new Date().toISOString(),
          },
        }),
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

    // Update campaign status if all variants reviewed
    if (pendingCount === 0) {
      const newStatus = approvedCount > 0 ? 'APPROVED' : 'READY';
      await prisma.campaign.update({
        where: { id: variant.campaignId },
        data: { status: newStatus },
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
    console.error('Error rejecting variant:', error);

    if ((error as any)?.code === 'P2025') {
      return NextResponse.json(
        { error: 'Variant not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to reject variant' },
      { status: 500 }
    );
  }
}
