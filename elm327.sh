#!/bin/bash
# From https://github.com/Ircama/ELM327-emulator
# Checking Python version (should be 3.5 or higher)
python3 -V

# Installing prerequisites
python3 -m pip install pyyaml
python3 -m pip install git+https://github.com/brendan-w/python-OBD.git # this is needed for obd_dictionary.py

# Downloading ELM327-emulator
git clone https://github.com/ircama/ELM327-emulator.git
cd ELM327-emulator
python3 -m elm &