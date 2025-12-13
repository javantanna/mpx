#!/bin/bash

# ================================================
# MPX File Association Setup (Linux)
# ================================================

echo "🔗 Setting up .mpx file association for VLC..."

# Check if VLC is installed
if ! command -v vlc &> /dev/null; then
    echo "❌ VLC not found. Installing VLC..."
    
    # Detect package manager and install
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y vlc
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y vlc
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm vlc
    else
        echo "⚠️  Please install VLC manually: sudo apt install vlc"
        exit 1
    fi
fi

echo "✅ VLC found: $(which vlc)"

# Create .desktop file for MPX
DESKTOP_FILE="$HOME/.local/share/applications/mpx-vlc.desktop"

mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=VLC Media Player (MPX)
Comment=Open MPX files with VLC
Exec=vlc %U
Icon=vlc
Terminal=false
Categories=AudioVideo;Player;Recorder;
MimeType=video/mpx;video/mp4;
NoDisplay=true
EOF

echo "✅ Created desktop entry: $DESKTOP_FILE"

# Update MIME database
echo "🔧 Registering .mpx MIME type..."

MIME_FILE="$HOME/.local/share/mime/packages/mpx.xml"
mkdir -p "$HOME/.local/share/mime/packages"

cat > "$MIME_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="video/mpx">
    <comment>MPX Video File</comment>
    <glob pattern="*.mpx"/>
    <sub-class-of type="video/mp4"/>
  </mime-type>
</mime-info>
EOF

update-mime-database "$HOME/.local/share/mime"

# Associate .mpx with VLC
xdg-mime default mpx-vlc.desktop video/mpx

# Update desktop database
update-desktop-database "$HOME/.local/share/applications"

echo ""
echo "🎉 Setup complete!"
echo "   .mpx files will now open in VLC Media Player"
echo ""
echo "💡 Test it:"
echo "   xdg-open your_video.mpx"
echo ""
