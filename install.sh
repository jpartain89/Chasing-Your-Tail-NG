#!/bin/bash
# Chasing Your Tail (CYT) - Unified Installation Script
# This script installs all required dependencies and sets up the system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           CHASING YOUR TAIL (CYT) INSTALLER                  ║"
    echo "║                Wi-Fi Surveillance Detection                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[STEP $1]${NC} $2"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root. Some operations will be performed with sudo."
        SUDO=""
    else
        SUDO="sudo"
        log_info "Running as user. Some operations will require sudo."
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif [[ -f /etc/lsb-release ]]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    log_info "Detected OS: $OS $VER"
}

install_system_dependencies() {
    log_step "1" "Installing System Dependencies"
    
    if command -v apt-get &> /dev/null; then
        log_info "Using apt-get package manager"
        $SUDO apt-get update
        $SUDO apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-tk \
            wireless-tools \
            iw \
            net-tools \
            pandoc \
            git \
            curl \
            gpsd \
            gpsd-clients
    elif command -v yum &> /dev/null; then
        log_info "Using yum package manager"
        $SUDO yum update -y
        $SUDO yum install -y \
            python3 \
            python3-pip \
            python3-tkinter \
            wireless-tools \
            iw \
            net-tools \
            pandoc \
            git \
            curl \
            gpsd \
            gpsd-clients
    elif command -v pacman &> /dev/null; then
        log_info "Using pacman package manager"
        $SUDO pacman -Sy --noconfirm \
            python \
            python-pip \
            tk \
            wireless_tools \
            iw \
            net-tools \
            pandoc \
            git \
            curl \
            gpsd
    else
        log_warn "Unknown package manager. Please install dependencies manually:"
        log_warn "  - python3, python3-pip, python3-tk"
        log_warn "  - wireless-tools, iw, net-tools"
        log_warn "  - pandoc, git, curl, gpsd"
    fi
}

install_kismet() {
    log_step "2" "Installing/Checking Kismet"
    
    if command -v kismet &> /dev/null; then
        log_info "Kismet is already installed: $(kismet --version 2>&1 | head -1)"
    else
        log_info "Kismet not found. Attempting to install..."
        
        if command -v apt-get &> /dev/null; then
            # Try installing from default repository first
            log_info "Attempting to install Kismet from system repository..."
            $SUDO apt-get install -y kismet 2>/dev/null || {
                # If not available, try adding Kismet repository
                log_info "Not in system repository, trying Kismet repository..."
                
                # Use modern method for GPG key (avoid deprecated apt-key)
                $SUDO mkdir -p /etc/apt/keyrings
                wget -qO - https://www.kismetwireless.net/repos/kismet-release.gpg.key 2>/dev/null | \
                    $SUDO gpg --dearmor -o /etc/apt/keyrings/kismet.gpg 2>/dev/null || {
                    log_warn "Could not add Kismet repository key."
                    log_warn "Please install Kismet manually from https://www.kismetwireless.net/"
                    return
                }
                
                # Try installing again
                $SUDO apt-get update 2>/dev/null
                $SUDO apt-get install -y kismet 2>/dev/null || {
                    log_warn "Could not install Kismet from repository."
                    log_warn "Please install Kismet manually from https://www.kismetwireless.net/"
                }
            }
        else
            log_warn "Please install Kismet manually from https://www.kismetwireless.net/"
        fi
    fi
}

install_python_dependencies() {
    log_step "3" "Installing Python Dependencies"
    
    # Check if requirements.txt exists
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
    
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        log_info "Installing Python packages from requirements.txt"
        pip3 install --user -r "$REQUIREMENTS_FILE"
    else
        log_info "Installing core Python packages"
        pip3 install --user requests cryptography
    fi
    
    log_info "Python dependencies installed successfully"
}

create_directories() {
    log_step "4" "Creating Required Directories"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    directories=(
        "$SCRIPT_DIR/logs"
        "$SCRIPT_DIR/reports"
        "$SCRIPT_DIR/ignore_lists"
        "$SCRIPT_DIR/kml_files"
        "$SCRIPT_DIR/surveillance_reports"
        "$SCRIPT_DIR/analysis_logs"
        "$SCRIPT_DIR/secure_credentials"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        else
            log_info "Directory exists: $dir"
        fi
    done
    
    # Set secure permissions on credentials directory
    chmod 700 "$SCRIPT_DIR/secure_credentials" 2>/dev/null || true
}

setup_wifi_permissions() {
    log_step "5" "Setting Up Wi-Fi Permissions"
    
    # Check if user is in required groups
    CURRENT_USER=$(whoami)
    
    if [[ $EUID -ne 0 ]]; then
        # Check for kismet group
        if getent group kismet &>/dev/null; then
            if ! groups "$CURRENT_USER" | grep -q kismet; then
                log_info "Adding user to kismet group..."
                $SUDO usermod -aG kismet "$CURRENT_USER"
                log_warn "You may need to log out and back in for group changes to take effect."
            else
                log_info "User already in kismet group"
            fi
        fi
        
        # Check for netdev group (common on Debian/Ubuntu)
        if getent group netdev &>/dev/null; then
            if ! groups "$CURRENT_USER" | grep -q netdev; then
                log_info "Adding user to netdev group..."
                $SUDO usermod -aG netdev "$CURRENT_USER"
            fi
        fi
    fi
}

verify_installation() {
    log_step "6" "Verifying Installation"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version)
        log_info "✅ Python installed: $PYTHON_VER"
    else
        log_error "❌ Python3 not found"
    fi
    
    # Check Tkinter
    if python3 -c "import tkinter" 2>/dev/null; then
        log_info "✅ Tkinter available"
    else
        log_error "❌ Tkinter not available. Please install python3-tk"
    fi
    
    # Check cryptography module
    if python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then
        log_info "✅ Cryptography module available"
    else
        log_error "❌ Cryptography module not available. Run: pip3 install cryptography"
    fi
    
    # Check requests module
    if python3 -c "import requests" 2>/dev/null; then
        log_info "✅ Requests module available"
    else
        log_error "❌ Requests module not available. Run: pip3 install requests"
    fi
    
    # Check Kismet
    if command -v kismet &> /dev/null; then
        log_info "✅ Kismet installed"
    else
        log_warn "⚠️ Kismet not found. Please install Kismet for full functionality."
    fi
    
    # Check core CYT files
    if [[ -f "$SCRIPT_DIR/chasing_your_tail.py" ]]; then
        log_info "✅ Core CYT module found"
    else
        log_error "❌ Core CYT module not found"
    fi
    
    if [[ -f "$SCRIPT_DIR/cyt_gui.py" ]]; then
        log_info "✅ GUI module found"
    else
        log_error "❌ GUI module not found"
    fi
}

print_next_steps() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              INSTALLATION COMPLETE! 🎉                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Run the setup wizard to configure CYT:"
    echo -e "   ${YELLOW}python3 cyt_gui.py${NC}"
    echo ""
    echo "2. Or run the command-line setup:"
    echo -e "   ${YELLOW}python3 setup_wizard.py${NC}"
    echo ""
    echo "3. To start monitoring (after setup):"
    echo -e "   ${YELLOW}python3 chasing_your_tail.py${NC}"
    echo ""
    echo "4. For surveillance analysis:"
    echo -e "   ${YELLOW}python3 surveillance_analyzer.py${NC}"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  - README.md    - User documentation"
    echo "  - CLAUDE.md    - Technical documentation"
    echo "  - SETUP.md     - Setup guide"
    echo ""
}

# Main installation flow
main() {
    print_banner
    
    log_info "Starting CYT installation..."
    log_info "Installation date: $(date)"
    
    check_root
    detect_os
    
    # Ask user for confirmation
    echo ""
    read -p "Do you want to proceed with installation? [Y/n] " -n 1 -r
    echo ""
    
    if [[ "${REPLY,,}" == "n" ]]; then
        log_info "Installation cancelled."
        exit 0
    fi
    
    install_system_dependencies
    install_kismet
    install_python_dependencies
    create_directories
    setup_wifi_permissions
    verify_installation
    print_next_steps
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "CYT Installer - Install Chasing Your Tail and all dependencies"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --verify       Only verify installation (don't install)"
        echo "  --deps-only    Only install dependencies"
        echo ""
        exit 0
        ;;
    --verify)
        print_banner
        check_root
        verify_installation
        exit 0
        ;;
    --deps-only)
        print_banner
        check_root
        detect_os
        install_system_dependencies
        install_python_dependencies
        exit 0
        ;;
    *)
        main
        ;;
esac
