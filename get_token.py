# Create an app in the RingCentral Developer Console. Make sure the app has all permissions enabled.
# Enter in the credentials for this app into the fields below.

# Test on localhost when needed. Can be any open port
PORT                  = 3000

# Production
RC_SERVER_URL        = 'https://platform.ringcentral.com'
RC_APP_CLIENT_ID         = 'Zu5g5Lbpd1UdYiJh0fjGB8'
RC_APP_CLIENT_SECRET     = '3Tkx8vkbu9meJtDudkH1rxdLc6bsxKI0Efe6vkyCXHuU'

# This credential is used for JWT-grant types
RC_USER_JWT               = 'eyJraWQiOiI4NzYyZjU5OGQwNTk0NGRiODZiZjVjYTk3ODA0NzYwOCIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJhdWQiOiJodHRwczovL3BsYXRmb3JtLnJpbmdjZW50cmFsLmNvbS9yZXN0YXBpL29hdXRoL3Rva2VuIiwic3ViIjoiMTQ0NzQ5NDAyMSIsImlzcyI6Imh0dHBzOi8vcGxhdGZvcm0ucmluZ2NlbnRyYWwuY29tIiwiZXhwIjozOTIzNzY2NjAwLCJpYXQiOjE3NzYyODI5NTMsImp0aSI6ImdPMWZKX1FFU3hxSE5ySW1mRGdVa1EifQ.E2QxQI87lo5GEtRCqXFhu9McXeyNpbgJZYSI0Yghab9d9bAgXmB84c4gtUqEF3QrWVr7rokvo34Soqkl6RHjVgo4wflpikg1o_3LU0JwZxA3PnSkAOLykxdjCXp_QZjxxefihP3FYMFi8Zi1RmqD6Zwoz9dNgu6YYQ4_BXk4pIGbjW2DBGT7RaD3P8ndZCZNwQRmNRbycm-KC5XyTqIiuwsX_5fnU2JFDq2ygB16KRL--aQbP2qKeehKnJa1gxhr08NF9YRVbgJSxrspA8FJHkF-23HXDLnkwStIbp-HDbOAWrkeHvlJtyi54aRcQhIDXmBeUeb89w9JT2lRlSTUdw'

# Used in messaging/quick-start.*
# For code testing purpose, we set the SMS recipient's phone number to this environment variable.
# You can set the phone number via this variable, or you can set it directly on your code.
SMS_RECIPIENT        = ''

# Used in messaging/send-fax.*
# For code testing purpose, we set the Fax recipient's phone number to this environment variable.
# You can set the phone number via this variable, or you can set it directly on your code.
FAX_RECIPIENT        = ''

# Used in voice/quick-start.*
# You can set the phone number via this variable, or you can set it directly on your code.

# For code testing purpose, we set the caller's phone number in this environment variable.
RINGOUT_CALLER      = ''

# For code testing purpose, we set the callee's phone number in this environment variable.
RINGOUT_RECIPIENT    = ''

# Used in voice/call-forwarding.*
# For code testing purpose, we set the forwarding phone number in this environment variable.
# You can set the phone number via this variable, or you can set it directly on your code.
FORWARDING_NUMBER = ''

# Used in code flow authentication Quick Start
# The following URL cannot be blank when running the code flow authentication Quick Start.
RC_REDIRECT_URL      = 'http://localhost:5000/oauth2callback'

# Used throughout AI (Artificial Intelligence API)
CONTENT_URI=https://github.com/ringcentral/ringcentral-api-docs/raw/main/resources/sample-calls.mp3
NGROK_URL=''
# Used in the Team Messaging bot code samples
# The following URL is your bot webhook delivery address
RC_BOT_WEBHOOK_URL = ''

# Used in the WebHook notification code samples
# The following URL is your webhook delivery address
WEBHOOK_DELIVERY_ADDRESS = ''

