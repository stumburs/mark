@echo off

:: Activate venv
call bot\venv\Scripts\activate

:: Run the bot
python bot\bot.py

:: Deactivate the venv
deactivate
