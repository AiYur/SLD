#!/usr/bin/env bash
# Sweet Diagnosis - start the app (macOS / Linux)
# Make it runnable once with:  chmod +x run_app.sh
# Then double-click it, or run:  ./run_app.sh

cd "$(dirname "$0")" || exit 1

# Use the local virtual environment if one was created (see README, Phase 2)
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Set SWEET_HOST=0.0.0.0 to let phones on the same Wi-Fi reach this laptop.
# export SWEET_HOST=0.0.0.0

python3 app.py
