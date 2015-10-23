from EthiopiaSMS import app
from flask import render_template, request, redirect, g
#from config import *
from twilio.rest import TwilioRestClient
from config import *
from database_helper import *


@app.route("/", methods=["GET","POST"])
def index():
  if request.method == "POST":

    # If they click the button to send a text message
    cell_number = request.form.get("cell_phone", None)
    text_message = request.form.get("text_message", None)

    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    call = client.calls.create(
      to=cell_number, 
      from_=FROM_NUMBER, 
      url="http://ethiopia-sms.herokuapp.com",  
      method="GET",  
      fallback_method="GET",  
      status_callback_method="GET",    
      record="false"
    ) 
     
    print call.sid

  return render_template("index.html")

@app.route("/users", methods=["GET","POST"])
def users():
  user_list = get_all_users()
  
  if request.method == "POST":
    ####################
    # For adding a new person into our database
    ####################
    cell_phone = request.form.get("cell_phone", None)
    name = request.form.get("name", None)
    
    user_entry = {
    "name": name,
    "cell_phone": cell_phone
    }

    # only add if all the fields are filled out
    if name != None:
      add_user(user_entry)


    ####################
    # For sending to a list of people selected on our front end
    ####################

    to_send = request.form.getlist("send", None)
    get_user_info_from_id_list(to_send)

    # Get all of the current users, updated from the database
    user_list = get_all_users()

  return render_template("users.html", user_list=user_list)

def send_to_list(database_users):
  message = "Hello my friend"
  for user_entry in database_users:
    send_message(message, user_entry.cell_phone)
    print "Succes"