import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "crm_logistic"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_logistic.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
