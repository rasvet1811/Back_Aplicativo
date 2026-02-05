@echo off
echo Iniciando servidor Django en http://localhost:8000
echo.
cd /d "%~dp0"
python manage.py runserver 0.0.0.0:8000
pause

