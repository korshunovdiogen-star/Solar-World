import sys
from pathlib import Path

# Микросервис использует обычные импорты (from database import ...),
# поэтому его папка должна быть в sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
