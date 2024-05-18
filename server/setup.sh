#!/bin/bash

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Create necessary directories
mkdir -p cache
mkdir -p logs

# Set up environment variables if needed
# export SOME_VAR=some_value

echo "Setup complete. Remember to activate the virtual environment with 'source venv/bin/activate' before running the project."