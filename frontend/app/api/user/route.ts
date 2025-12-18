import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// GET /api/user - Get current user info (returns first user for dev mode)
export async function GET(request: NextRequest) {
  try {
    // Dev mode: return first user or create default
    let user = await prisma.user.findFirst({
      select: {
        id: true,
        name: true,
        email: true,
        image: true,
      },
    });

    if (!user) {
      // Create default dev user
      user = await prisma.user.create({
        data: {
          email: 'dev@brandtruth.ai',
          name: 'Dev User',
        },
        select: {
          id: true,
          name: true,
          email: true,
          image: true,
        },
      });
    }

    return NextResponse.json({ user });
  } catch (error) {
    console.error('Failed to fetch user:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user' },
      { status: 500 }
    );
  }
}
