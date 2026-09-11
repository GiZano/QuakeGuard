#!/bin/bash

echo "🚀 Initializing QuakeGuard Command Center..."

# Get absolute paths dynamically based on script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Auto-generate secrets on first boot
if [[ ! -f "$PROJECT_ROOT/backend/.env" ]]; then
    echo "⚠️  First boot detected: backend/.env not found."
    echo "🔐 Running secret generator to provision fresh .env files..."
    "$SCRIPT_DIR/generate_secrets.sh"
    echo ""
fi

echo "🌐 Running tunnel automation..."
"$SCRIPT_DIR/tunnel_init.sh"
if [[ $? -ne 0 ]]; then
    echo "❌ Tunnel script failed. Aborting."
    exit 1
fi
echo ""

echo "🖥️ Opening 3 separate terminal windows (Ptyxis)..."

# 1. Backend Window
ptyxis --new-window -d "$PROJECT_ROOT/backend" -T "Backend (Docker)" -- bash -c "echo '=== BACKEND (Docker) ==='; docker compose --profile ai up --build; exec bash" &

# 2. Mobile Window
# Adding a small delay so windows don't overlap completely at spawn
sleep 0.5
ptyxis --new-window -d "$PROJECT_ROOT/mobile" -T "Mobile (Expo)" -- bash -c "echo '=== MOBILE (Expo) ==='; npx expo start --clear; exec bash" &

# 3. Firmware Window (Wait 30s for the Backend to be fully ready)
sleep 0.5
ptyxis --new-window -d "$PROJECT_ROOT/firmware" -T "IoT (ESP32)" -- bash -c "echo '=== IoT (ESP32) ==='; echo '⏳ Waiting 30 seconds for the backend to start...'; sleep 30; echo '🚀 Flashing new firmware with updated Cloudflare URL...'; pio run -t upload -t monitor; exec bash" &

echo ""
read -p "🎬 Do you want to start the Hollywood Simulator for Grafana? [y/N]: " run_hollywood
if [[ "$run_hollywood" =~ ^[Yy]$ ]]; then
    echo "🎥 Hollywood Simulator will launch in a new terminal..."
    sleep 0.5
    ptyxis --new-window -d "$PROJECT_ROOT" -T "Hollywood (Demo)" -- bash -c "echo '=== HOLLYWOOD SIMULATOR ==='; echo '⏳ Waiting 20 seconds for the backend to start...'; sleep 20; ./scripts/hollywood.sh; exec bash" &
fi

echo ""
echo "✅ All terminals launched successfully!"
echo ""
echo "🔗 QuakeGuard Command Center Links:"
echo " - 📚 Swagger API Docs: http://localhost:8000/docs"
echo " - 📊 Grafana Dashboard: http://localhost:3000"
echo ""
echo "🎛️ Command Center Console is active."
echo "Type a command to restart a component if a terminal was accidentally closed:"
echo "  'backend'   -> Relaunch Backend (Docker)"
echo "  'mobile'    -> Relaunch Mobile (Expo)"
echo "  'iot'       -> Relaunch Firmware (ESP32)"
echo "  'hollywood' -> Relaunch Hollywood Simulator"
echo "  'exit'      -> Close this Command Center"
echo ""

# Background job to wait for Grafana and open it (silenced output to not mess up the prompt)
(
  for i in {1..30}; do
    if curl -s http://localhost:3000/login > /dev/null; then
      if command -v xdg-open > /dev/null; then
          xdg-open "http://localhost:3000/d/quakeguard-mission-control/quakeguard-mission-control?orgId=1&refresh=5s" > /dev/null 2>&1 &
      elif command -v open > /dev/null; then
          open "http://localhost:3000/d/quakeguard-mission-control/quakeguard-mission-control?orgId=1&refresh=5s" > /dev/null 2>&1 &
      fi
      break
    fi
    sleep 2
  done
) &

while true; do
    read -p "QuakeGuard> " cmd
    case "$cmd" in
        backend)
            ptyxis --new-window -d "$PROJECT_ROOT/backend" -T "Backend (Docker)" -- bash -c "echo '=== BACKEND (Docker) ==='; docker compose --profile ai up --build; exec bash" &
            echo "🚀 Relaunched Backend window."
            ;;
        mobile)
            ptyxis --new-window -d "$PROJECT_ROOT/mobile" -T "Mobile (Expo)" -- bash -c "echo '=== MOBILE (Expo) ==='; npx expo start --clear; exec bash" &
            echo "🚀 Relaunched Mobile window."
            ;;
        iot)
            ptyxis --new-window -d "$PROJECT_ROOT/firmware" -T "IoT (ESP32)" -- bash -c "echo '=== IoT (ESP32) ==='; pio run -t upload -t monitor; exec bash" &
            echo "🚀 Relaunched Firmware window."
            ;;
        hollywood)
            ptyxis --new-window -d "$PROJECT_ROOT" -T "Hollywood (Demo)" -- bash -c "echo '=== HOLLYWOOD SIMULATOR ==='; ./scripts/hollywood.sh; exec bash" &
            echo "🚀 Relaunched Hollywood Simulator window."
            ;;
        exit|quit)
            echo "👋 Closing Command Center. Goodbye!"
            break
            ;;
        *)
            if [[ -n "$cmd" ]]; then
                echo "❌ Unknown command. Available: backend, mobile, iot, hollywood, exit"
            fi
            ;;
    esac
done
