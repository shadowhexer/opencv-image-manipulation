# activate venv (use absolute path if necessary)
# note: exec replaces the shell so Python inherits the stdio fds
# Depending if you are in Linux or Windows, you may need to change the directory 
# and the command to activate the virtual environment. This is currently in Linux.
cd ~/Documents/CSC_126/App_Development/image-manipulation/python && . .venv/bin/activate
exec python main.py
