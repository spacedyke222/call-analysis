#!/usr/bin/env python
from ringcentral import SDK
from dotenv import load_dotenv
import os, sys

load_dotenv()

print("DEBUG SERVER:", os.environ.get("RC_SERVER_URL"))

rcsdk = SDK(
    os.environ.get("RC_APP_CLIENT_ID"),
    os.environ.get("RC_APP_CLIENT_SECRET"),
    os.environ.get("RC_SERVER_URL")
)

platform = rcsdk.platform()

try:
    platform.login(jwt=os.environ.get("RC_USER_JWT"))
except Exception as e:
    sys.exit("Auth failed: " + str(e))

print("Login with JWT successful.")
