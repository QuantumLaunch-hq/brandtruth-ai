import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import prisma from '@/lib/db';

// GET /api/campaigns - List campaigns for the current user
export async function GET(request: NextRequest) {
  try {
    const session = await auth();

    // For testing: if no session, return all campaigns
    let userId: string | undefined;

    if (session?.user?.email) {
      const user = await prisma.user.findUnique({
        where: { email: session.user.email },
      });
      userId = user?.id;
    }

    // Fetch campaigns (filtered by user if logged in, all if not)
    const campaigns = await prisma.campaign.findMany({
      where: userId ? { userId } : {},
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
    const session = await auth();

    const body = await request.json();
    const { name, url } = body;

    if (!name || !url) {
      return NextResponse.json(
        { error: 'Name and URL are required' },
        { status: 400 }
      );
    }

    // Get or create default user for testing
    let user = session?.user?.email
      ? await prisma.user.findUnique({ where: { email: session.user.email } })
      : await prisma.user.findFirst();

    if (!user) {
      // Create a default test user
      user = await prisma.user.create({
        data: {
          email: 'test@brandtruth.ai',
          name: 'Test User',
        },
      });
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
