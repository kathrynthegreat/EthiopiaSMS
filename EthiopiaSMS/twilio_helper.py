# send a testing message to phone
from twilio.rest import TwilioRestClient
from EthiopiaSMS.config import *

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)


def send_call(to_number, db_id):
    # fallback_url = ("http://twimlets.com/holdmusic"
    #                 "?Bucket=com.twilio.music.ambient")
    # fallback_url = "http://ethiopia-sms.herokuapp.com/voice?caller={}&question=init".format(db_id)
    fallback_url = "http://ethiopia-sms.herokuapp.com/ivr/welcome?caller={}".format(db_id)
    # fallback_url = "http://twimlbin.com/1d82ef38d1cbcc856bf35d6ebcbdd3ba"

    call = client.calls.create(
        from_=FROM_NUMBER_DR,
        to=to_number,
        url=fallback_url,
        record=False
    )

    return call.sid


def get_call_logs():
    return client.calls.list()


def get_logs_csv():
    csv_request_url = ('https://api.twilio.com/2010-04-01/Accounts/{}'
                       '/Calls.csv').format(ACCOUNT_SID)
    return csv_request_url
