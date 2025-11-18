@echo off
echo ========================================
echo  VANET Speed Dashboard - Quick Start
echo ========================================
echo.
echo Starting application...
echo.
"C:/Users/srina/ANACONDAMINI/Scripts/conda.exe" run -n vanet310 --no-capture-output python -m streamlit run streamlit_clean_dashboard.py --server.port 8505
pause
