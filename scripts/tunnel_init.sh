#!/bin/bash

echo "🚀 Starting Cloudflare tunnel in background..."
# Kill any dangling tunnel processes
killall cloudflared 2>/dev/null

# Launch tunnel and redirect output to a temporary log file
cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflare_tunnel.log 2>&1 &

echo "⏳ Waiting for URL generation (might take a few seconds)..."

# Poll for the URL for up to 30 seconds
URL=""
for i in {1..30}; do
    # Extract just the domain e.g. "word-word.trycloudflare.com" (force text mode with -a)
    URL=$(grep -a -oP 'https://\K[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cloudflare_tunnel.log | head -n 1)
    if [[ -n "$URL" ]]; then
        break
    fi
    sleep 1
done

if [[ -z "$URL" ]]; then
    echo "❌ Error: Failed to retrieve Cloudflare URL. Check /tmp/cloudflare_tunnel.log" >&2
    exit 1
fi

echo "✅ URL generated: https://$URL"

# Get project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Update Mobile app configuration
if [[ -f "$PROJECT_ROOT/mobile/.env" ]]; then
    # Replace the base API URL line
    sed -i "s|^EXPO_PUBLIC_API_BASE_URL=.*|EXPO_PUBLIC_API_BASE_URL=https://$URL|" "$PROJECT_ROOT/mobile/.env"
    echo "📱 Updated mobile/.env"
else
    echo "⚠️ Warning: mobile/.env not found at $PROJECT_ROOT/mobile/.env!"
fi

# 2. Update ESP32 firmware configuration
if [[ -f "$PROJECT_ROOT/firmware/esp32_config.env" ]]; then
    sed -i "s|^SERVER_HOST=.*|SERVER_HOST=\"$URL\"|" "$PROJECT_ROOT/firmware/esp32_config.env"
    sed -i "s|^SERVER_PROTOCOL=.*|SERVER_PROTOCOL=\"https\"|" "$PROJECT_ROOT/firmware/esp32_config.env"
    sed -i "s|^SERVER_PORT=.*|SERVER_PORT=443|" "$PROJECT_ROOT/firmware/esp32_config.env"
    echo "🔌 Updated firmware/esp32_config.env"
else
    echo "⚠️ Warning: firmware/esp32_config.env not found at $PROJECT_ROOT/firmware/esp32_config.env!"
fi


echo ""
echo "🎉 Everything configured automatically!"
echo "👉 ESP32: Go to the 'firmware' folder and run 'pio run -t upload'"
echo "👉 Mobile: If Expo is running, press 'r' to reload, otherwise 'npx expo start'"
echo "👉 To stop the tunnel when finished: killall cloudflared"

echo ""
echo "📱 Inquadra questo QR dall'app per auto-configurare il server:"
qrencode -t ANSIUTF8 "https://$URL"
echo ""

