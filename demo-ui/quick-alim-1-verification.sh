#!/bin/bash
# quick-alim-1-verification.sh
# Run this after deployment to verify ALİM 1 setup

echo "🚀 ALİM 1 Verification Checklist"
echo "================================"
echo ""

# Check 1: Avatar files exist
echo "✓ Checking avatar files..."
if [ -f "demo-ui/public/avatars/alim_1.svg" ]; then
    echo "  ✅ alim_1.svg exists"
else
    echo "  ❌ alim_1.svg MISSING"
fi

if [ -f "demo-ui/public/avatars/general.svg" ]; then
    echo "  ✅ general.svg exists"
else
    echo "  ❌ general.svg MISSING"
fi

# Check 2: Config mentions ALİM 1
echo ""
echo "✓ Checking config.toml..."
if grep -q "name = \"ALİM 1\"" demo-ui/.chainlit/config.toml; then
    echo "  ✅ Product name is ALİM 1"
else
    echo "  ❌ Product name not ALİM 1"
fi

if grep -q "ALİM 1 — ALİM Assistant" demo-ui/.chainlit/config.toml; then
    echo "  ✅ Description mentions ALİM 1"
else
    echo "  ❌ Description doesn't mention ALİM 1"
fi

# Check 3: Code doesn't have stale action callbacks
echo ""
echo "✓ Checking for deprecated patterns..."
if grep -q "@cl.action_callback(\"weather\")" demo-ui/app.py; then
    echo "  ❌ STALE: Found @cl.action_callback (should be removed)"
else
    echo "  ✅ No stale action callbacks"
fi

# Check 4: Code uses ALİM 1 as author
echo ""
echo "✓ Checking ALİM 1 references..."
count=$(grep -c "author=\"ALİM 1\"" demo-ui/app.py)
if [ $count -ge 2 ]; then
    echo "  ✅ Found $count instances of author=\"ALİM 1\""
else
    echo "  ⚠️  Only found $count instances (expected ≥2)"
fi

# Check 5: CSS is updated
echo ""
echo "✓ Checking CSS selectors..."
if grep -q ".cl-message\[data-author=\"ALİM 1\"\]" demo-ui/public/custom.css; then
    echo "  ✅ CSS has ALİM 1 selectors"
else
    echo "  ⚠️  CSS might not have ALİM 1 selectors"
fi

echo ""
echo "================================"
echo "🎯 Next Steps:"
echo "1. Refresh browser (Ctrl+Shift+R)"
echo "2. Check ALİM 1 avatar displays"
echo "3. Check profile selector works"
echo "4. Check starters update per profile"
echo ""
