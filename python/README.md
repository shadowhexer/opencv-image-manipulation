# Virtual Environment
**Note:** *For development mode only. Modify the extensions Path in `neutralino.config.json` and point it to the `ext-runner.sh` file.*

Steps to create a virtual environment:
1. Create a virtual environment within this folder by running `python3 -m venv venv`.
2. Edit the `ext-runner.sh` in the resources folder and point it to the `activate` file. 

    **Note:** *This is based on Linux. Windows script may differ.*
    
3. Install the dependencies using `pip install -r requirements.txt`.
4. Every time run Neutralino (`neu run`), it will automatically activate the Virtual Environment using the script.


# Build the project
1. Install the dependencies first as outlined in previous steps if they are not yet installed.
2. Open the terminal in this directory.
3. Run `pyinstaller main.py --clean --onefile --noconfirm --distpath /path/to/image-manipulation/resources/extensions/python --runtime-tmpdir ./resources/extensions/python/_pyruntime --exclude-module tkinter --exclude-module test --hidden-import=cv2 --hidden-import=numpy --hidden-import=PIL --collect-all numpy --collect-all scipy`. Change `/path/to` with root directory of your desktop.

    **Explanation:** PyInstaller is used to build the Python project. `pyinstaller <name of the enty file>.py` is the default command. Options used includes:

    * `--clean` for removing previous builds and caches.
    * `--onefile` for compiling the project into a single file. Alternative is `--onedir` for compiling the project into a single folder.
    * `--distpath /path/to/resources/extensions/python` to export the file/folder to the specific directory.
    * `--runtime-tmpdir ./resources/extensions/python/_pyruntime` to create a custom temporary directory to hold runtime files and folders. 

    Read the rest of options in the [PyInstaller documentation page](https://pyinstaller.org/en/stable/index.html) for more info.

