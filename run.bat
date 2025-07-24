@echo off

:: Check if venv exists
if not exist "bot\venv\Scripts\activate" (
    echo Creating virtual environment...
    python -m venv bot\venv
)

:: Activate venv
call bot\venv\Scripts\activate

:: Install dependencies
echo Installing dependencies...
pip install --upgrade -r  bot\requirements.txt

:: Run the bot
python bot\bot.py

:: Deactivate the venv
deactivate