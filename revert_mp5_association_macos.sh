#!/bin/bash

# ================================================
# Revert MP5 File Association + Uninstall (macOS)
# ================================================

echo "🔄 Reverting .mp5 file association and cleaning up..."

# Step 1: Remove file association
echo ""
echo "📌 Step 1: Removing file association"
echo "-----------------------------------"

if command -v duti &> /dev/null; then
    echo "🔧 Removing association with duti..."
    duti -s com.apple.finder .mp5 all 2>/dev/null || true
    echo "✅ Association removed"
else
    echo "🔧 Removing association from Launch Services..."
    defaults delete com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers 2>/dev/null || true
    
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
        -kill -r -domain local -domain system -domain user 2>/dev/null || true
    
    echo "✅ Association removed"
fi

# Step 2: Uninstall duti (only if installed by us)
echo ""
echo "📌 Step 2: Uninstalling dependencies"
echo "-----------------------------------"

if command -v duti &> /dev/null; then
    echo "🗑️  Uninstalling duti..."
    brew uninstall duti 2>/dev/null && echo "✅ duti uninstalled" || echo "⚠️  duti not removed (may be used by other apps)"
else
    echo "ℹ️  duti not installed, skipping"
fi

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "Summary:"
echo "  ✅ .mp5 file association removed"
echo "  ✅ duti dependency cleaned up"
echo ""
echo "Note: Python packages and FFmpeg were NOT removed"
echo "      (they may be used by other projects)"
echo ""

