import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// PATCH /api/campaigns/[id]/variants/[variantId] - Update variant (approve/reject)
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; variantId: string }> }
) {
  try {
    const { id, variantId } = await params;
    const body = await request.json();
    const { status, headline, primaryText, cta } = body;

    // Verify variant belongs to campaign
    const existing = await prisma.variant.findFirst({
      where: { id: variantId, campaignId: id },
    });

    if (!existing) {
      return NextResponse.json(
        { error: 'Variant not found' },
        { status: 404 }
      );
    }

    // Validate status if provided
    if (status && !['PENDING', 'APPROVED', 'REJECTED'].includes(status)) {
      return NextResponse.json(
        { error: 'Invalid status' },
        { status: 400 }
      );
    }

    // Update variant
    const variant = await prisma.variant.update({
      where: { id: variantId },
      data: {
        ...(status && { status }),
        ...(headline && { headline }),
        ...(primaryText && { primaryText }),
        ...(cta && { cta }),
      },
    });

    return NextResponse.json({ variant });
  } catch (error) {
    console.error('Failed to update variant:', error);
    return NextResponse.json(
      { error: 'Failed to update variant' },
      { status: 500 }
    );
  }
}
