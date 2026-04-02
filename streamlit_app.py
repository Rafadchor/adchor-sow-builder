import os

# Force UTF-8 for ALL Python I/O on this process -- prevents ascii codec errors
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

import runpy, sys

_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

runpy.run_path(os.path.join(_app_dir, "app.py"), run_name="__main__")
