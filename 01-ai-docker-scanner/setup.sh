#!/bin/bash
# Quick installation script for AI Docker Security Scanner

echo "🚀 AI Docker Security Scanner - Quick Setup"
echo "=========================================="
echo ""

# Check if running on macOS or Linux
OS="$(uname -s)"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo "Checking Python..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Docker
echo ""
echo "Checking Docker..."
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo "✅ Docker $DOCKER_VERSION found"
else
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

# Check/Install Trivy
echo ""
echo "Checking Trivy..."
if command_exists trivy; then
    TRIVY_VERSION=$(trivy --version | head -1 | cut -d' ' -f2)
    echo "✅ Trivy $TRIVY_VERSION found"
else
    echo "⚠️  Trivy not found. Installing..."
    
    if [ "$OS" = "Darwin" ]; then
        # macOS
        if command_exists brew; then
            brew install trivy
        else
            echo "❌ Homebrew not found. Install from: https://brew.sh"
            exit 1
        fi
    elif [ "$OS" = "Linux" ]; then
        # Linux
        sudo apt-get update
        sudo apt-get install wget apt-transport-https gnupg lsb-release -y
        wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
        echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
        sudo apt-get update
        sudo apt-get install trivy -y
    else
        echo "❌ Unsupported OS. Install Trivy manually from: https://aquasecurity.github.io/trivy"
        exit 1
    fi
    
    echo "✅ Trivy installed"
fi

# Check/Install Ollama
echo ""
echo "Checking Ollama..."
if command_exists ollama; then
    echo "✅ Ollama found"
else
    echo "⚠️  Ollama not found. Installing..."
    
    if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "❌ Please install Ollama manually from: https://ollama.com"
        exit 1
    fi
    
    echo "✅ Ollama installed"
fi

# Check if Ollama is running
echo ""
echo "Checking if Ollama is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running. Starting Ollama in background..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama started successfully"
    else
        echo "❌ Failed to start Ollama. Please run 'ollama serve' manually"
        exit 1
    fi
fi

# Download Llama 3.2 model
echo ""
echo "Checking Llama 3.2 model..."
if ollama list | grep -q "llama3.2"; then
    echo "✅ Llama 3.2 model already downloaded"
else
    echo "⚠️  Downloading Llama 3.2 model (~2GB, this may take a few minutes)..."
    ollama pull llama3.2
    echo "✅ Llama 3.2 model downloaded"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✅ Python dependencies installed"

# Make the scanner executable
chmod +x src/docker_scanner.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Try it out:"
echo "  python3 src/docker_scanner.py nginx:latest"
echo ""
echo "For more options:"
echo "  python3 src/docker_scanner.py --help"
echo ""
