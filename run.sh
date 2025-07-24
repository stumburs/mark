#!/bin/bash

# Check if venv exists
if [ ! -f "bot/venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv bot/venv
fi

# Activate venv
source bot/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade -r bot/requirements.txt

# Run the bot
python3 bot/bot.py

# Deactivate venv
deactivate