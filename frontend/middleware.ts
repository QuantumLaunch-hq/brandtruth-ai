import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';

// Routes that require authentication
// Temporarily disabled for testing
const protectedRoutes: string[] = [
  // '/campaigns',
  // '/studio',
  // '/dashboard',
];

// Routes that should redirect to /campaigns if already logged in
const authRoutes = ['/login'];

export default auth((req) => {
  const { nextUrl } = req;
  const isLoggedIn = !!req.auth;

  // Check if the route is protected
  const isProtectedRoute = protectedRoutes.some(route =>
    nextUrl.pathname.startsWith(route)
  );

  // Check if the route is an auth route (login/register)
  const isAuthRoute = authRoutes.some(route =>
    nextUrl.pathname.startsWith(route)
  );

  // Redirect to login if trying to access protected route while not logged in
  if (isProtectedRoute && !isLoggedIn) {
    const loginUrl = new URL('/login', nextUrl.origin);
    loginUrl.searchParams.set('callbackUrl', nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect to campaigns if trying to access auth route while logged in
  // Disabled - let users access login page even if logged in (to fix session issues)
  // if (isAuthRoute && isLoggedIn) {
  //   return NextResponse.redirect(new URL('/campaigns', nextUrl.origin));
  // }

  return NextResponse.next();
});

export const config = {
  matcher: [
    // Match all routes except static files and API routes
    '/((?!_next/static|_next/image|favicon.ico|api/auth).*)',
  ],
};
