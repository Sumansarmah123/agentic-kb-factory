#!/bin/bash
# Build Verification Script for Agentic KB Factory
# Checks all components before deployment

set -e  # Exit on error

echo "🔍 Agentic KB Factory - Build Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python
echo "1. Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    pass "Python installed: $PYTHON_VERSION"
else
    fail "Python 3 not found"
fi

# Check Node.js
echo ""
echo "2. Checking Node.js environment..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    pass "Node.js installed: $NODE_VERSION"
else
    fail "Node.js not found"
fi

# Check backend files
echo ""
echo "3. Checking backend structure..."
[ -f "backend/main.py" ] && pass "main.py exists" || fail "main.py missing"
[ -f "backend/config.py" ] && pass "config.py exists" || fail "config.py missing"
[ -f "backend/observability.py" ] && pass "observability.py exists" || fail "observability.py missing"
[ -f "backend/services/gemini_secured.py" ] && pass "gemini_secured.py exists" || fail "gemini_secured.py missing"
[ -f "backend/services/model_armor.py" ] && pass "model_armor.py exists" || fail "model_armor.py missing"

# Check frontend files
echo ""
echo "4. Checking frontend structure..."
[ -f "frontend/package.json" ] && pass "package.json exists" || fail "package.json missing"
[ -f "frontend/vite.config.ts" ] && pass "vite.config.ts exists" || fail "vite.config.ts missing"
[ -f "frontend/src/main.tsx" ] && pass "main.tsx exists" || fail "main.tsx missing"
[ -f "frontend/src/components/Dashboard.tsx" ] && pass "Dashboard.tsx exists" || fail "Dashboard.tsx missing"
[ -f "frontend/src/components/SelfHealingDemo.tsx" ] && pass "SelfHealingDemo.tsx exists (KEY)" || fail "SelfHealingDemo.tsx missing"

# Check environment file
echo ""
echo "5. Checking configuration..."
if [ -f ".env" ]; then
    pass ".env file exists"
    
    # Check required variables
    if grep -q "GCP_PROJECT_ID" .env; then
        pass "GCP_PROJECT_ID configured"
    else
        warn "GCP_PROJECT_ID not found in .env"
    fi
    
    if grep -q "GEMINI_API_KEY" .env; then
        pass "GEMINI_API_KEY configured"
    else
        warn "GEMINI_API_KEY not found in .env"
    fi
else
    warn ".env file not found (okay for Cloud Run deployment)"
fi

# Check dependencies
echo ""
echo "6. Checking dependencies..."
if [ -f "venv/bin/activate" ] || [ -f "venv/Scripts/activate" ]; then
    pass "Python venv exists"
else
    warn "Python venv not found - run: python -m venv venv"
fi

if [ -d "frontend/node_modules" ]; then
    pass "Node modules installed"
else
    warn "Node modules not found - run: cd frontend && npm install"
fi

# Check tests
echo ""
echo "7. Checking tests..."
if [ -f "backend/tests/test_integration.py" ]; then
    pass "Integration tests exist"
    
    # Count test functions
    TEST_COUNT=$(grep -c "async def test_" backend/tests/test_integration.py || true)
    pass "Found $TEST_COUNT test scenarios"
else
    fail "Integration tests missing"
fi

# Try building frontend
echo ""
echo "8. Verifying frontend build..."
cd frontend
if npm run build > /dev/null 2>&1; then
    pass "Frontend builds successfully"
    
    if [ -d "dist" ]; then
        pass "dist/ directory created"
        
        # Check critical files
        [ -f "dist/index.html" ] && pass "index.html built" || warn "index.html missing"
        [ -d "dist/assets" ] && pass "assets/ directory exists" || warn "assets/ missing"
    else
        fail "dist/ directory not created"
    fi
else
    fail "Frontend build failed"
fi
cd ..

# Check Dockerfile
echo ""
echo "9. Checking deployment files..."
[ -f "Dockerfile" ] && pass "Dockerfile exists" || fail "Dockerfile missing"
[ -f "requirements.txt" ] && pass "requirements.txt exists" || fail "requirements.txt missing"
[ -f "cloudbuild.yaml" ] && pass "cloudbuild.yaml exists" || warn "cloudbuild.yaml missing (optional)"

# Check documentation
echo ""
echo "10. Checking documentation..."
[ -f "README.md" ] && pass "README.md exists" || fail "README.md missing"
[ -f "DEPLOYMENT_GUIDE.md" ] && pass "DEPLOYMENT_GUIDE.md exists" || warn "DEPLOYMENT_GUIDE.md recommended"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Build verification complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start backend: cd backend && python -m uvicorn main:app --reload"
echo "2. Start frontend: cd frontend && npm run dev"
echo "3. Run tests: pytest"
echo "4. Deploy to Cloud Run: gcloud run deploy agentic-kb-factory --source ."
echo ""
