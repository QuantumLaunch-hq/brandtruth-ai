import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import prisma from '@/lib/db';

// POST /api/campaigns/save - Save a complete campaign with variants
// If campaign with workflowId already exists (created by workflow), UPDATE it instead of CREATE
export async function POST(request: NextRequest) {
  try {
    const session = await auth();
    const body = await request.json();

    const {
      name,
      url,
      workflowId,
      status,
      brandProfile,
      budgetResult,
      audienceResult,
      variants,
    } = body;

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
      user = await prisma.user.create({
        data: {
          email: 'test@brandtruth.ai',
          name: 'Test User',
        },
      });
    }

    // Check if campaign already exists (created by workflow)
    let existingCampaign = null;
    if (workflowId) {
      existingCampaign = await prisma.campaign.findUnique({
        where: { workflowId },
        include: { variants: true },
      });
    }

    // If campaign exists, UPDATE it instead of creating duplicate
    if (existingCampaign) {
      console.log(`[API] Campaign exists for workflow ${workflowId}, updating...`);

      const campaign = await prisma.$transaction(async (tx) => {
        // Update campaign with frontend data (status, etc.)
        const updated = await tx.campaign.update({
          where: { id: existingCampaign.id },
          data: {
            name,
            status: status || existingCampaign.status,
            brandProfile: brandProfile || existingCampaign.brandProfile,
            budgetResult: budgetResult || existingCampaign.budgetResult,
            audienceResult: audienceResult || existingCampaign.audienceResult,
            updatedAt: new Date(),
          },
        });

        // Update variant statuses if provided
        if (variants && variants.length > 0) {
          for (const v of variants) {
            await tx.variant.updateMany({
              where: {
                campaignId: existingCampaign.id,
                id: v.id,
              },
              data: {
                status: v.status || 'PENDING',
                updatedAt: new Date(),
              },
            });
          }
        }

        return tx.campaign.findUnique({
          where: { id: updated.id },
          include: { variants: true },
        });
      });

      console.log(`[API] Campaign updated: ${campaign?.id}`);
      return NextResponse.json({ campaign, updated: true }, { status: 200 });
    }

    // No existing campaign - create new one
    const campaign = await prisma.$transaction(async (tx) => {
      // Create the campaign
      const newCampaign = await tx.campaign.create({
        data: {
          name,
          url,
          workflowId: workflowId || null,
          status: status || 'READY',
          brandProfile: brandProfile || null,
          budgetResult: budgetResult || null,
          audienceResult: audienceResult || null,
          userId: user!.id,
          completedAt: new Date(),
        },
      });

      // Create variants if provided
      if (variants && variants.length > 0) {
        await tx.variant.createMany({
          data: variants.map((v: any) => ({
            id: v.id, // Preserve the original variant ID from workflow
            campaignId: newCampaign.id,
            headline: v.headline,
            primaryText: v.primaryText,
            cta: v.cta,
            angle: v.angle || null,
            emotion: v.emotion || null,
            imageUrl: v.imageUrl || null,
            composedUrl: v.composedUrl || null,
            score: v.score || null,
            scoreDetails: v.scoreDetails || null,
            status: v.status || 'PENDING',
          })),
        });
      }

      // Return campaign with variants
      return tx.campaign.findUnique({
        where: { id: newCampaign.id },
        include: {
          variants: true,
        },
      });
    });

    console.log(`[API] Campaign saved: ${campaign?.id} with ${campaign?.variants.length} variants`);

    return NextResponse.json({ campaign }, { status: 201 });
  } catch (error) {
    console.error('Failed to save campaign:', error);
    return NextResponse.json(
      { error: 'Failed to save campaign' },
      { status: 500 }
    );
  }
}
