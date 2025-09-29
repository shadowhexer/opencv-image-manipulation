# activate venv (use absolute path if necessary)
# note: exec replaces the shell so Python inherits the stdio fds
cd ~/Documents/CSC_126/App_Development/image-manipulation/python && . .venv/bin/activate
exec python main.py
