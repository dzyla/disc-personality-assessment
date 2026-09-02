"""Entry point kept at the original path so `streamlit run disc_style.py` works.

The application lives in `app/` (Streamlit shell) and `assessment/` (pure
scoring and reporting logic, importable and testable without Streamlit).
"""

from app.main import main

main()
