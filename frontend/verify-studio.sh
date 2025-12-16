#!/bin/bash

# BrandTruth Studio - Quick Test Script
# Run this to verify the Studio is working

echo "=========================================="
echo "BrandTruth Studio - Verification Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this from frontend directory"
    exit 1
fi

# Check dependencies
echo "1. Checking dependencies..."
if grep -q "framer-motion" package.json; then
    echo "   ✅ framer-motion installed"
else
    echo "   ❌ framer-motion missing - run: npm install framer-motion"
    exit 1
fi

# Check Studio files exist
echo ""
echo "2. Checking Studio files..."
if [ -f "app/studio/page.tsx" ]; then
    echo "   ✅ app/studio/page.tsx exists"
else
    echo "   ❌ app/studio/page.tsx missing"
    exit 1
fi

# Check test file exists
echo ""
echo "3. Checking test files..."
if [ -f "__tests__/studio/Studio.test.tsx" ]; then
    echo "   ✅ __tests__/studio/Studio.test.tsx exists"
else
    echo "   ❌ Studio tests missing"
fi

if [ -f "e2e/studio.spec.ts" ]; then
    echo "   ✅ e2e/studio.spec.ts exists"
else
    echo "   ❌ E2E tests missing"
fi

# Check if dev server can start
echo ""
echo "4. Build check..."
npm run build 2>&1 | tail -5

echo ""
echo "=========================================="
echo "Verification complete!"
echo ""
echo "To run the Studio:"
echo "  npm run dev"
echo "  Open: http://localhost:3000/studio"
echo ""
echo "To run tests:"
echo "  npm test -- --testPathPattern=studio"
echo "  npm run test:e2e -- studio.spec.ts"
echo "=========================================="
