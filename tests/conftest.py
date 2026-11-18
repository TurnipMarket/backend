"""Config común de los tests: base temporal, clave JWT falsa y sys.path."""
import os
import sys
import tempfile
from pathlib import Path
 
_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_PATH", str(Path(_tmp) / "test.db"))
os.environ.setdefault("UPLOAD_DIR", str(Path(_tmp) / "uploads"))
os.environ.setdefault("JWT_SECRET", "x" * 40)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))