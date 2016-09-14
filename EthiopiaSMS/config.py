import os
import logging

logging.basicConfig(level=logging.INFO)

ACCOUNT_SID = os.environ["ACCOUNT_SID"]
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
FROM_NUMBER_SA = os.environ["FROM_NUMBER_SA"]
FROM_NUMBER_DR = os.environ["FROM_NUMBER_DR"]
DATABASE_URL = os.environ["DATABASE_URL"]
AUTH_USERNAME = os.environ["AUTH_USERNAME"]
AUTH_PASSWORD = os.environ["AUTH_PASSWORD"]
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')
