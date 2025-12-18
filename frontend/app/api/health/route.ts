import { NextResponse } from 'next/server';

// GET /api/health - Health check endpoint for container orchestration
export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'brandtruth-frontend',
  });
}
