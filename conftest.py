"""Put the repository root on sys.path.

The Streamlit app imports `app` and `assessment` as top-level packages. When
Streamlit runs disc_style.py it adds the script's directory itself; under pytest
nothing does, and AppTest executes the script in-process.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
