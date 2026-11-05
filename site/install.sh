#!/bin/bash
# Token Deck installer. Read it before you run it.
set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
  echo "Token Deck's installer supports macOS 12 or later." >&2
  exit 1
fi
major=$(sw_vers -productVersion | cut -d. -f1)
if [ "$major" -lt 12 ]; then
  echo "Token Deck's installer supports macOS 12 or later." >&2
  exit 1
fi

arch="${TOKENDECK_ARCH:-}"
if [ -z "$arch" ]; then
  if [ "$(sysctl -in hw.optional.arm64)" = "1" ]; then arch="arm64"; else arch="x64"; fi
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
base="https://github.com/stiggio/token-deck/releases/latest/download"
zip="TokenDeck-mac-${arch}.zip"
curl -fL "$base/$zip" -o "$tmp/$zip"
curl -fL "$base/${zip}.sha256" -o "$tmp/${zip}.sha256"
cd "$tmp"
expected=$(awk '{print $1}' "${zip}.sha256")
actual=$(shasum -a 256 "$zip" | awk '{print $1}')
if [ "$expected" != "$actual" ]; then
  echo "Checksum mismatch: nothing was changed. Run the command again." >&2
  exit 1
fi

osascript -e 'tell application "Token Deck" to quit' >/dev/null 2>&1 || true
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if ! pgrep -x "Token Deck" >/dev/null 2>&1; then break; fi
  sleep 1
done

ditto -x -k "$zip" "$tmp/unpack"
app=$(find "$tmp/unpack" -name 'Token Deck.app' -maxdepth 3 | head -1)
if [ -z "$app" ]; then
  echo "The archive did not contain Token Deck.app" >&2
  exit 1
fi

dest="/Applications/Token Deck.app"
if [ ! -w "/Applications" ]; then dest="$HOME/Applications/Token Deck.app"; mkdir -p "$HOME/Applications"; fi
rm -rf "$dest"
ditto "$app" "$dest"
xattr -dr com.apple.quarantine "$dest" || true
open "$dest"
echo "Installed Token Deck to $dest and opened it."
