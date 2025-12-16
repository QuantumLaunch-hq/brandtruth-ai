import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import prisma from '@/lib/db';

// GET /api/campaigns - List campaigns for the current user
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get user from session email
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Fetch campaigns with variant counts
    const campaigns = await prisma.campaign.findMany({
      where: { userId: user.id },
      include: {
        variants: {
          select: {
            id: true,
            status: true,
          },
        },
        _count: {
          select: { variants: true },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    // Transform to response format
    const response = campaigns.map(campaign => ({
      id: campaign.id,
      name: campaign.name,
      url: campaign.url,
      status: campaign.status,
      variantCount: campaign._count.variants,
      approvedCount: campaign.variants.filter(v => v.status === 'APPROVED').length,
      createdAt: campaign.createdAt.toISOString(),
      updatedAt: campaign.updatedAt.toISOString(),
      completedAt: campaign.completedAt?.toISOString() || null,
      workflowId: campaign.workflowId,
    }));

    return NextResponse.json({ campaigns: response });
  } catch (error) {
    console.error('Failed to fetch campaigns:', error);
    return NextResponse.json(
      { error: 'Failed to fetch campaigns' },
      { status: 500 }
    );
  }
}

// POST /api/campaigns - Create a new campaign (optional - workflow creates campaigns)
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { name, url } = body;

    if (!name || !url) {
      return NextResponse.json(
        { error: 'Name and URL are required' },
        { status: 400 }
      );
    }

    // Get user from session email
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Create campaign
    const campaign = await prisma.campaign.create({
      data: {
        name,
        url,
        userId: user.id,
        status: 'DRAFT',
      },
    });

    return NextResponse.json({ campaign }, { status: 201 });
  } catch (error) {
    console.error('Failed to create campaign:', error);
    return NextResponse.json(
      { error: 'Failed to create campaign' },
      { status: 500 }
    );
  }
}
