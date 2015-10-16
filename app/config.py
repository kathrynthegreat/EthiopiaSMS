import os
import logging

logging.basicConfig(level=logging.INFO)

ACCOUNT_SID = os.environ["ACCOUNT_SID"]
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
TO_NUMBER = os.environ["TO_NUMBER"]
FROM_NUMBER = os.environ["FROM_NUMBER"]
