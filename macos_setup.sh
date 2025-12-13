#!/bin/bash


# ================================================
# Python Environment + FFmpeg Setup (macOS)
# ================================================

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}       Python Environment + FFmpeg Setup${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# ---------------------------------------------------
# Step 1: Check if Python is installed
# ---------------------------------------------------

echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed.${NC}"
    echo -e "${YELLOW}Install Python 3 using Homebrew: brew install python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}Python found: $PYTHON_VERSION${NC}"
echo ""
# ---------------------------------------------------
# Step 2: Create virtual environment (.venv)
# ---------------------------------------------------

if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists: .venv${NC}"
    echo -e "${YELLOW}Skipping creation...${NC}"
    echo ""
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    
    python3 -m venv .venv
    
    echo -e "${GREEN}Virtual environment created: .venv${NC}"
    echo ""
fi


# ---------------------------------------------------
# Step 3: Activate venv and install requirements
# ---------------------------------------------------


echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo -e "${GREEN}Requirements installed successfully.${NC}"
echo ""

# ---------------------------------------------------
# Step 4: Check if FFmpeg is installed
# ---------------------------------------------------
echo -e "${YELLOW}Checking FFmpeg installation...${NC} (Now this is going to be tough)"
if command -v ffmpeg &> /dev/null; 
then
    FFMPEG_VERSION=$(ffmpeg --version | head -n 1)
    echo -e "${GREEN}FFmpeg found sweet: $FFMPEG_VERSION${NC}"
    echo ""

    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}Setup Complete!${NC}"
    echo -e "${CYAN}================================================${NC}"
    exit 0
fi

echo -e "${YELLOW}sus FFmpeg NOT installed now its a hassel.${NC}"
echo ""

# ---------------------------------------------------
# Step 5: Check if Homebrew is installed
# ---------------------------------------------------

echo -e "${YELLOW}Checking for Homebrew...${NC}"

if ! command -v brew &> /dev/null;
then
    echo -e "${RED}ERROR: man are you a noob? Homebrew is also not Installed${NC}"
    echo ""
    # ------------------------------
    # Auto-install Homebrew
    # ------------------------------
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    echo ""
    echo -e "${GREEN}Homebrew installation complete.${NC}"
    echo ""

    # ------------------------------
    # Add Homebrew to PATH (Apple Silicon + Intel support)
    # ------------------------------

    if [ -d "/opt/homebrew/bin" ]; 
    then
        # Apple Silicon
        echo -e "${YELLOW}Adding /opt/homebrew/bin to PATH...${NC}"
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile

        export PATH="/opt/homebrew/bin:$PATH"

    elif [ -d "/usr/local/bin" ]
    then
         # Intel mac
        echo -e "${YELLOW}Adding /usr/local/bin to PATH...${NC}"
        echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zprofile
        export PATH="/usr/local/bin:$PATH"
    fi
    # Refresh shell config
    source ~/.zprofile || true

    # Double Check

    if ! command -v brew &> /dev/null;
    then
        echo -e "${RED}ERROR: Homebrew installation failed. Install manually:${NC}"
        echo -e "${CYAN}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
        exit 1
    fi

else
    echo -e "${GREEN}Homebrew found.${NC}"
fi

echo ""


# ---------------------------------------------------
# Step 6: Install FFmpeg using Homebrew
# ---------------------------------------------------
echo -e "${YELLOW}Installing FFmpeg using Homebrew...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"
echo ""

brew install ffmpeg
if [ $? -eq 0 ];
then
    echo ""
    echo -e "${GREEN}FFmpeg installation complete.${NC}"

    # Verify Installation
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo -e "${GREEN}Installed: $FFMPEG_VERSION${NC}"
else
    echo -e "${RED}ERROR: FFmpeg installation failed.${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Setup Complete!${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""
echo -e "${GREEN}woof finally end of the setup now the fun part run main.py of mpx_gui.py!${NC}"
echo ""
exit 0


