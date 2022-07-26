#!/bin/bash

# docker run -ti --rm -v $(pwd):/workspace -w /workspace arm32v7/python:3 sh -c ""

pip3 install pyinstaller
pip3 install -r requirements.pip
python3 -m PyInstaller -y watch.py
