# Install Python3 virtualenv or venv with pip 
# Navigate to home directory of the project.
# Run the following commands on terminal for setting up Virtual-Environment for the project.
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# At this point env should be activated with all the required libraries installed.
# Run the following command for running the app.

python dashboard.py

# browse to the http://127.0.0.1:8050/ to access the Dashboard.
