import importlib, sys, os

# Force re-execution of app modules on every Streamlit rerun
for _mod in ['app', 'brief_extractor', 'sow_generator', 'sow_pdf']:
    if _mod in sys.modules:
        del sys.modules[_mod]

from app import *
