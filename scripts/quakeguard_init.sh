#!/bin/bash

# ==============================================================================
# CONSOLE MODE: Executed ONLY in the Top-Right pane
# ==============================================================================
if [[ "$1" == "--console" ]]; then
    SESSION="quakeguard-cc"
    PROJECT_ROOT="$2"

    # Function to print the QR Code
    print_qr() {
        if [[ -f /tmp/qg_tunnel_output.log ]]; then
            cat /tmp/qg_tunnel_output.log
            echo "---------------------------------------------------------"
        else
            echo "❌ No QR Code found in /tmp/qg_tunnel_output.log"
        fi
        return 0
    }

    # Function to print the Menu
    print_menu() {
        echo "✅ QuakeGuard Command Center Active!"
        echo "🔗 Quick Links:"
        echo " - 📚 Swagger API: http://localhost:8000/docs"
        echo " - 📊 Grafana: http://localhost:3000"
        echo ""
        echo "🎛️ Available commands:"
        echo "  'backend'   -> Restart Docker (Top-Left)"
        echo "  'mobile'    -> Restart Expo (Bottom-Left)"
        echo "  'iot'       -> Restart ESP32 (Bottom-Right)"
        echo "  'hollywood' -> Launch/Restart Hollywood (Hidden Tab #1)"
        echo "  'qr'        -> Show Cloudflare tunnel QR Code"
        echo "  'help/menu' -> Show this command list"
        echo "  'exit'      -> Close everything and exit"
        echo ""
        return 0
    }

    clear
    print_qr
    print_menu

    while true; do
        read -p "QuakeGuard> " cmd
        case "$cmd" in
            backend)
                tmux send-keys -t $SESSION:0.0 C-c
                tmux send-keys -t $SESSION:0.0 "docker compose --profile ai up --build" C-m
                echo "🚀 Backend restarted."
                ;;
            mobile)
                tmux send-keys -t $SESSION:0.1 C-c
                tmux send-keys -t $SESSION:0.1 "npx expo start --clear" C-m
                echo "🚀 Mobile (Expo) restarted."
                ;;
            iot)
                tmux send-keys -t $SESSION:0.3 C-c
                tmux send-keys -t $SESSION:0.3 "pio run -t upload -t monitor" C-m
                echo "🚀 Firmware restarted."
                ;;
            hollywood)
                tmux kill-window -t $SESSION:1 2>/dev/null
                tmux new-window -t $SESSION -n "Hollywood" "cd '$PROJECT_ROOT' && ./scripts/hollywood.sh"
                tmux select-window -t $SESSION:0
                echo "🚀 Hollywood Simulator launched! (Press Ctrl+B, then 1 to view. Ctrl+B, then 0 to return)."
                ;;
            qr)
                clear
                print_qr
                ;;
            help|menu)
                print_menu
                ;;
            exit|quit)
                echo "👋 Closing Command Center..."
                tmux kill-session -t $SESSION 2>/dev/null
                break
                ;;
            *)
                if [[ -n "$cmd" ]]; then
                    echo "❌ Unknown command. Type 'help' or 'menu' for the command list."
                fi
                ;;
        esac
    done
    exit 0
fi

# ==============================================================================
# STANDARD MODE: Environment setup and Tmux grid generation
# ==============================================================================

echo "🚀 Initializing QuakeGuard Command Center..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ ! -f "$PROJECT_ROOT/backend/.env" ]]; then
    echo "⚠️  First boot detected: backend/.env not found."
    echo "🔐 Running secret generator..."
    "$SCRIPT_DIR/generate_secrets.sh"
    echo ""
fi

# Capture the tunnel output (including QR) into the temporary file
echo "🌐 Running tunnel automation..."
"$SCRIPT_DIR/tunnel_init.sh" | tee /tmp/qg_tunnel_output.log
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    echo "❌ Tunnel script failed. Aborting."
    exit 1
fi
echo ""

echo "🖥️ Transforming current terminal into the Tmux dashboard..."

SESSION="quakeguard-cc"
tmux kill-session -t $SESSION 2>/dev/null

# 1. Pane 0: Backend (Top-Left)
tmux new-session -d -s $SESSION -c "$PROJECT_ROOT/backend"
tmux send-keys -t $SESSION:0.0 "echo '=== BACKEND (Docker) ===' && docker compose --profile ai up --build" C-m

# 📌 ENABLE MOUSE SUPPORT IN TMUX (For scrolling and pane selection)
tmux set-option -g mouse on

# Split in half (Creates the Right side)
tmux split-window -h -t $SESSION -c "$PROJECT_ROOT"

# 2. Split the Left half in two -> Pane 1: Mobile (Bottom-Left)
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION:0.0 -c "$PROJECT_ROOT/mobile"
tmux send-keys -t $SESSION:0.1 "echo '=== MOBILE (Expo) ===' && npx expo start --clear" C-m

# 3. Split the Right half in two -> Pane 3: IoT (Bottom-Right)
tmux select-pane -t $SESSION:0.2
tmux split-window -v -t $SESSION:0.2 -c "$PROJECT_ROOT/firmware"
tmux send-keys -t $SESSION:0.3 "echo '=== IoT (ESP32) ===' && echo '⏳ Waiting 30s...' && sleep 30 && pio run -t upload -t monitor" C-m

# 4. Pane 2 (Top-Right): Start the interactive Console
tmux send-keys -t $SESSION:0.2 "\"$BASH_SOURCE\" --console \"$PROJECT_ROOT\"" C-m

# Set final focus on the Console (Top-Right)
tmux select-pane -t $SESSION:0.2

# Background job to open Grafana
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

# Attach the terminal to the Tmux session
exec tmux attach-session -t $SESSION