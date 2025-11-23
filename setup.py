"""
Setup script for NFL Betting System
====================================

This is a minimal setup.py for development mode installation.
"""

from setuptools import setup, find_packages

setup(
    name="nfl-betting-system",
    version="0.1.0",
    description="NFL Betting System with XGBoost",
    author="NFL Betting System",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10,<3.13",
    install_requires=[
        "nfl-data-py>=0.3.0",
        "pandas>=2.0.0",
        "pyarrow>=12.0.0",
        "numpy>=1.24.0,<2.0.0",  # Pin to avoid compilation issues
        "xgboost>=2.0.0",
        "scikit-learn>=1.3.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "requests>=2.31.0",
        "requests-cache>=1.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "black>=23.7.0",
            "ruff>=0.0.280",
            "mypy>=1.4.0",
        ]
    },
)


