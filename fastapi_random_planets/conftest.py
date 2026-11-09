import sys
from pathlib import Path

# Микросервис импортирует модули напрямую, поэтому его папка должна быть в sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
