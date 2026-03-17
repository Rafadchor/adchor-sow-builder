import runpy, os

# Always re-execute app.py fresh — bypasses Python module cache entirely
runpy.run_path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"),
    run_name="__main__"
)
