import os
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_RESULTS_PER_PAGE = int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "50"))
ADZUNA_BATCH_SIZE = int(os.getenv("ADZUNA_BATCH_SIZE", "10"))
ADZUNA_BATCH_DELAY = float(os.getenv("ADZUNA_BATCH_DELAY", "0.1"))
ADZUNA_MAX_PAGES = int(os.getenv("ADZUNA_MAX_PAGES", "50"))

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TTL = int(os.getenv("REDIS_TTL", "3600"))