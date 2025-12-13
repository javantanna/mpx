#!/bin/bash

# ================================================
# Revert MPX File Association + Uninstall (Linux)
# ================================================

echo "🔄 Reverting .mpx file association and cleaning up..."

# Step 1: Remove file association
echo ""
echo "📌 Step 1: Removing file association"
echo "-----------------------------------"

# Remove MIME type association
if [ -f "$HOME/.local/share/mime/packages/mpx.xml" ]; then
    echo "🔧 Removing MIME type..."
    rm -f "$HOME/.local/share/mime/packages/mpx.xml"
    update-mime-database "$HOME/.local/share/mime" 2>/dev/null || true
    echo "✅ MIME type removed"
else
    echo "ℹ️  MIME type not found, skipping"
fi

# Remove desktop entry
if [ -f "$HOME/.local/share/applications/mpx-vlc.desktop" ]; then
    echo "🔧 Removing desktop entry..."
    rm -f "$HOME/.local/share/applications/mpx-vlc.desktop"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    echo "✅ Desktop entry removed"
else
    echo "ℹ️  Desktop entry not found, skipping"
fi

# Reset default application
xdg-mime default "" video/mpx 2>/dev/null || true

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "Summary:"
echo "  ✅ .mpx file association removed"
echo "  ✅ MIME type and desktop entries cleaned up"
echo ""
echo "Note: Python packages and FFmpeg were NOT removed"
echo "      (they may be used by other projects)"
echo ""


