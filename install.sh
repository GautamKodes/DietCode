#!/bin/bash
set -e

INSTALL_DIR="$HOME/.dietcode"
mkdir -p "$INSTALL_DIR"

python -m venv "$INSTALL_DIR/venv"

"$INSTALL_DIR/venv/bin/pip" install --index-url https://download.pytorch.org/whl/cpu torch
"$INSTALL_DIR/venv/bin/pip" install .

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat << 'EOF' > "$BIN_DIR/dietcode"
#!/bin/bash
exec "$HOME/.dietcode/venv/bin/dietcode" "$@"
EOF

chmod +x "$BIN_DIR/dietcode"

echo "DietCode installed successfully!"
echo "Make sure $BIN_DIR is in your PATH."
echo "You can now run 'dietcode' globally from any directory."

OLLAMA_INSTALLED=true
if ! command -v ollama >/dev/null 2>&1; then
    OLLAMA_INSTALLED=false
fi

MODEL_PULLED=false
if [ "$OLLAMA_INSTALLED" = true ]; then
    if ollama list 2>/dev/null | grep -q "qwen2.5-coder:1.5b"; then
        MODEL_PULLED=true
    fi
fi

if [ "$OLLAMA_INSTALLED" = false ] || [ "$MODEL_PULLED" = false ]; then
    echo ""
    echo "=================================================="
    echo "🤖 Optional AI Summary Assistant Configuration"
    echo "=================================================="
    echo "DietCode uses Qwen2.5-Coder (1.5B) via Ollama to generate"
    echo "high-fidelity 1-sentence summaries for your files."
    echo ""
    if [ "$OLLAMA_INSTALLED" = false ]; then
        echo "❌ Ollama is not installed on this system."
    else
        echo "✓ Ollama is installed, but the 'qwen2.5-coder:1.5b' model is missing."
    fi
    echo ""
    read -p "Would you like to install/configure Ollama and download the model now? [y/N]: " choice
    case "$choice" in
        [yY][eE][sS]|[yY])
            if [ "$OLLAMA_INSTALLED" = false ]; then
                echo "Installing Ollama (requires sudo access)..."
                if curl -fsSL https://ollama.com/install.sh | sh; then
                    echo "✓ Ollama installed successfully."
                    OLLAMA_INSTALLED=true
                else
                    echo "⚠️ Failed to install Ollama automatically. You may need to install it manually."
                fi
            fi
            
            if [ "$OLLAMA_INSTALLED" = true ]; then
                echo "Starting Ollama service if not already running..."
                if command -v systemctl >/dev/null 2>&1; then
                    sudo systemctl start ollama || true
                fi
                echo "Pulling 'qwen2.5-coder:1.5b' (approx. 900MB)..."
                ollama pull qwen2.5-coder:1.5b
                echo "✓ Model pulled successfully."
            fi
            ;;
        *)
            echo ""
            echo "Skipping AI assistant setup. DietCode will use static heuristics to map"
            echo "your files. You can always configure Ollama later by running:"
            echo "  1. Install Ollama:  curl -fsSL https://ollama.com/install.sh | sh"
            echo "  2. Pull the model:   ollama pull qwen2.5-coder:1.5b"
            echo "=================================================="
            ;;
    esac
fi
