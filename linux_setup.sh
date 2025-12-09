#!/bin/bash

# ================================================
# Python Environment + FFmpeg Setup (Linux)
# ================================================

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}      Python Environment + FFmpeg Setup (Linux)${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# ---------------------------------------------------
# Step 1: Detect Linux Distribution
# ---------------------------------------------------
OS="unknown"

if [[ -e /etc/os-release ]]; then
    source /etc/os-release
    OS=$ID
fi

echo -e "${YELLOW}Detected Linux distro: ${CYAN}${OS}${NC}"
echo ""

# ---------------------------------------------------
# Step 2: Check Python Installation
# ---------------------------------------------------
echo -e "${YELLOW}Checking Python installation...${NC}"

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}ERROR: Python3 is not installed.${NC}"
    echo -e "${YELLOW}Install Python3 for your system:${NC}"
    echo -e "${CYAN}Ubuntu/Debian: sudo apt install python3 python3-venv${NC}"
    echo -e "${CYAN}Fedora/RHEL: sudo dnf install python3 python3-venv${NC}"
    echo -e "${CYAN}Arch: sudo pacman -S python${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}Python found: $PYTHON_VERSION${NC}"
echo ""

# ---------------------------------------------------
# Step 3: Create Virtual Environment (.venv)
# ---------------------------------------------------
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists: .venv${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

echo ""

# ---------------------------------------------------
# Step 4: Activate venv and install requirements
# ---------------------------------------------------
echo -e "${YELLOW}Activating venv and installing requirements...${NC}"

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo -e "${GREEN}Python dependencies installed successfully.${NC}"
echo ""

# ---------------------------------------------------
# Step 5: Check if FFmpeg is installed
# ---------------------------------------------------
echo -e "${YELLOW}Checking for FFmpeg...${NC}"

if command -v ffmpeg &>/dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo -e "${GREEN}FFmpeg found: $FFMPEG_VERSION${NC}"
    echo ""
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}Setup Complete!${NC}"
    echo -e "${CYAN}================================================${NC}"
    exit 0
fi

echo -e "${RED}FFmpeg NOT installed.${NC}"
echo ""

# ---------------------------------------------------
# Step 6: Install FFmpeg (auto based on distro)
# ---------------------------------------------------
echo -e "${YELLOW}Installing FFmpeg for ${OS}...${NC}"

case "$OS" in
    ubuntu|debian|kali|linuxmint|pop)
        sudo apt update
        sudo apt install -y ffmpeg
        ;;
    fedora)
        sudo dnf install -y ffmpeg
        ;;
    rhel|rocky|almalinux)
        sudo dnf config-manager --set-enabled crb || true
        sudo dnf install -y epel-release || true
        sudo dnf install -y ffmpeg || true
        ;;
    arch|manjaro)
        sudo pacman -Sy --needed ffmpeg
        ;;
    opensuse*)
        sudo zypper install -y ffmpeg
        ;;
    *)
        echo -e "${YELLOW}Unknown distro. Attempting fallback: Linuxbrew (Homebrew for Linux)...${NC}"
        if ! command -v brew &>/dev/null; then
            echo -e "${YELLOW}Installing Linuxbrew...${NC}"
            NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        fi

        brew install ffmpeg
        ;;
esac

echo ""
echo -e "${GREEN}FFmpeg installation complete.${NC}"
echo ""

# Confirm installation
FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
echo -e "${GREEN}Installed: $FFMPEG_VERSION${NC}"

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Setup Complete! Linux install ready.${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""
echo -e "${GREEN}woof finally! Now run main.py or mp5_gui.py 😎${NC}"
echo ""

exit 0
