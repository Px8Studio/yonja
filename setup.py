"""
Minimal setup.py for Streamlit Cloud compatibility.
The actual package configuration is in pyproject.toml.
This file is needed because Streamlit Cloud's pip install . 
doesn't properly handle src-layout packages without it.
"""
from setuptools import setup

if __name__ == "__main__":
    setup()
