#!/bin/bash

# ================================================
# MP5 File Association Setup (macOS)
# ================================================

echo "🔗 Setting up .mp5 file association for VLC..."

# Check if VLC is installed
VLC_PATH=""

if [ -d "/Applications/VLC.app" ]; then
    VLC_PATH="/Applications/VLC.app"
elif [ -d "$HOME/Applications/VLC.app" ]; then
    VLC_PATH="$HOME/Applications/VLC.app"
else
    echo "❌ VLC not found. Please install VLC Media Player first."
    echo "   Download from: https://www.videolan.org/vlc/"
    exit 1
fi

echo "✅ VLC found at: $VLC_PATH"

# Install duti if not present (for file association)
if ! command -v duti &> /dev/null; then
    echo "📦 Installing duti (file association utility)..."
    if command -v brew &> /dev/null; then
        brew install duti
    else
        echo "⚠️  Homebrew not found. Using manual method..."
    fi
fi

# Method 1: Using duti (preferred)
if command -v duti &> /dev/null; then
    echo "🔧 Associating .mp5 files with VLC using duti..."
    duti -s org.videolan.vlc .mp5 all
    echo "✅ Association created with duti"
else
    # Method 2: Using defaults (fallback)
    echo "🔧 Associating .mp5 files with VLC using defaults..."
    defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add \
        '{LSHandlerContentType=public.movie;LSHandlerRoleAll=org.videolan.vlc;}'
    
    # Rebuild Launch Services database
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
        -kill -r -domain local -domain system -domain user
    
    echo "✅ Association created with defaults"
fi

echo ""
echo "🎉 Setup complete!"
echo "   .mp5 files will now open in VLC Media Player"
echo ""
echo "💡 Test it:"
echo "   1. Double-click any .mp5 file"
echo "   2. Or run: open -a VLC your_video.mp5"
echo ""
