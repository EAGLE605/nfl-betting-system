#!/bin/bash
echo "============================================"
echo "NFL Edge Finder - Authenticated Dashboard"
echo "============================================"
echo ""
echo "Starting secure authentication system..."
echo ""
echo "Admin Access: b_flink@hotmail.com"
echo "Password: Stevie2019!"
echo ""
echo "Opening in browser at http://localhost:8501"
echo ""
source .venv/bin/activate
streamlit run dashboard/app_complete.py

