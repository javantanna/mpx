#!/bin/bash

# ================================================
# MP5 File Association Setup (Linux)
# ================================================

echo "🔗 Setting up .mp5 file association for VLC..."

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

# Create .desktop file for MP5
DESKTOP_FILE="$HOME/.local/share/applications/mp5-vlc.desktop"

mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=VLC Media Player (MP5)
Comment=Open MP5 files with VLC
Exec=vlc %U
Icon=vlc
Terminal=false
Categories=AudioVideo;Player;Recorder;
MimeType=video/mp5;video/mp4;
NoDisplay=true
EOF

echo "✅ Created desktop entry: $DESKTOP_FILE"

# Update MIME database
echo "🔧 Registering .mp5 MIME type..."

MIME_FILE="$HOME/.local/share/mime/packages/mp5.xml"
mkdir -p "$HOME/.local/share/mime/packages"

cat > "$MIME_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="video/mp5">
    <comment>MP5 Video File</comment>
    <glob pattern="*.mp5"/>
    <sub-class-of type="video/mp4"/>
  </mime-type>
</mime-info>
EOF

update-mime-database "$HOME/.local/share/mime"

# Associate .mp5 with VLC
xdg-mime default mp5-vlc.desktop video/mp5

# Update desktop database
update-desktop-database "$HOME/.local/share/applications"

echo ""
echo "🎉 Setup complete!"
echo "   .mp5 files will now open in VLC Media Player"
echo ""
echo "💡 Test it:"
echo "   xdg-open your_video.mp5"
echo ""
