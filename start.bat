@echo off
echo Starting Claims Management System...
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Starting Django development server...
echo.
echo Access the application at: http://127.0.0.1:8001/
echo Admin panel at: http://127.0.0.1:8001/admin/
echo.
echo Test users:
echo   admin/admin123 (Admin)
echo   john.smith/password123 (Write)
echo   jane.doe/password123 (Write)
echo   bob.wilson/password123 (Read+Export)
echo   alice.brown/password123 (Read Only)
echo.
python manage.py runserver 8001
