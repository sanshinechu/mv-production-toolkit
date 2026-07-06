@echo off
cd /d "%~dp0.."
python scripts\wan_local_i2v_bridge.py --scene 1 --submit --wait
pause
