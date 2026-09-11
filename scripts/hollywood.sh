#!/bin/bash
echo "🎬 Starting QuakeGuard Hollywood Simulator..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ ! -d "$PROJECT_ROOT/backend/.venv" ]]; then
    echo "❌ Error: Backend virtual environment not found. Start the backend first." >&2
    exit 1
fi

source "$PROJECT_ROOT/backend/.venv/bin/activate"
export PYTHONPATH="$PROJECT_ROOT/backend"

echo "🌍 Ensuring world zones are seeded in PostgreSQL..."
python "$SCRIPT_DIR/seed_world_zones.py"

python "$SCRIPT_DIR/hollywood.py"
