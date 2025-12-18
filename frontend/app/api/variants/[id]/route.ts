import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// GET /api/variants/[id] - Get variant by ID
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const variant = await prisma.variant.findUnique({
      where: { id: params.id },
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

    if (!variant) {
      return NextResponse.json(
        { error: 'Variant not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ variant });
  } catch (error) {
    console.error('Error fetching variant:', error);
    return NextResponse.json(
      { error: 'Failed to fetch variant' },
      { status: 500 }
    );
  }
}

// PATCH /api/variants/[id] - Update variant status
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { status } = body;

    // Validate status
    if (!['PENDING', 'APPROVED', 'REJECTED'].includes(status)) {
      return NextResponse.json(
        { error: 'Invalid status. Must be PENDING, APPROVED, or REJECTED' },
        { status: 400 }
      );
    }

    // Update variant
    const variant = await prisma.variant.update({
      where: { id: params.id },
      data: {
        status,
        updatedAt: new Date(),
      },
      include: {
        campaign: {
          select: {
            id: true,
            name: true,
          },
        },
      },
    });

    // Check if all variants in campaign are reviewed (none pending)
    const pendingCount = await prisma.variant.count({
      where: {
        campaignId: variant.campaignId,
        status: 'PENDING',
      },
    });

    // Check if any variants are approved
    const approvedCount = await prisma.variant.count({
      where: {
        campaignId: variant.campaignId,
        status: 'APPROVED',
      },
    });

    // Update campaign status if all variants reviewed
    if (pendingCount === 0 && approvedCount > 0) {
      await prisma.campaign.update({
        where: { id: variant.campaignId },
        data: { status: 'APPROVED' },
      });
    }

    return NextResponse.json({
      variant,
      campaign: {
        pendingCount,
        approvedCount,
        allReviewed: pendingCount === 0,
      },
    });
  } catch (error) {
    console.error('Error updating variant:', error);

    // Handle not found
    if ((error as any)?.code === 'P2025') {
      return NextResponse.json(
        { error: 'Variant not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to update variant' },
      { status: 500 }
    );
  }
}
