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
