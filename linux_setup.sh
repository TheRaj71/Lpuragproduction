#!/bin/bash

# Increase inotify watch limit
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Install system dependencies
sudo apt-get update
sudo apt-get install -y sqlite3 python3-pip python3-dev build-essential python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

echo "Setup complete! Run 'streamlit run app.py' to start the application."
