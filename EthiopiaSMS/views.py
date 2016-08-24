from EthiopiaSMS import app
from flask import render_template, request, redirect, url_for, Response, make_response
from werkzeug import secure_filename
from twilio.rest import TwilioRestClient
from twilio import twiml
import subprocess
from EthiopiaSMS.config import *
from EthiopiaSMS.database_helper import *
from EthiopiaSMS.twilio_helper import *
import datetime
import json
import time
import io

user_list = None
call_list = None
ethiopia_info = {
    "regions": ["Afar", "Amhara"],
    "villages": [],
    "message": ""
}

def write_questions(questions):
  with open(os.path.join(APP_STATIC,'questions.json')) as f:
    q_data = json.load(f)
  if questions['init']:
    q_data['init'] = questions['init']

  if questions['1']:
    q_data['1'] = questions['1']

  if questions['2']:
    q_data['2'] = questions['2']

  if questions['3']:
    q_data['3'] = questions['3']

  with io.open(os.path.join(APP_STATIC,'questions.json'), 'w', encoding='utf8') as f:
    f.write(json.dumps(q_data, ensure_ascii=False))


def get_questions():
  with open(os.path.join(APP_STATIC,'questions.json')) as f:
    q_data = json.load(f)

  return q_data


question_info = get_questions()


# app.config['BASIC_AUTH_USERNAME'] = USERNAME
# app.config['BASIC_AUTH_PASSWORD'] = PASSWORD

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# basic_auth = BasicAuth(app)


def allowed_file(filename):
    return '.' in filename

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        # If they click the button to send a text message
        cell_number = request.form.get("cell_phone", None)

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

        print (call.sid)

    return render_template("index.html")


def check_user(user_entry):
    # simple check on user info
    if user_entry["name"] == None or user_entry["cell_phone"] == None or \
    user_entry["region"] == None or user_entry["village"] == None:
        return False
    for name_part in user_entry["name"].split(" "):
        if not name_part.isalpha():
            return False
    if not user_entry["cell_phone"].isnumeric():
        return False
    for region_part in user_entry["region"].split(" "):
        if not region_part.isalpha():
            return False
    for village_part in user_entry["village"].split(" "):
        if not village_part.isalpha():
            return False
    return True


@app.route("/users", methods=["GET", "POST"])
def users():
    date = datetime.datetime.utcnow()
    date = date + datetime.timedelta(hours=3)
    date = date.strftime("%a %I:%M%p %d %B %Y")
    ethiopia_info["time_string"] = date

    if request.method == "POST":
        ####################
        # For adding a new person into our database
        ####################
        cell_phone = request.form.get("cell_phone", None)
        name = request.form.get("name", None)
        input_region = request.form.get("regions", None)
        input_village = request.form.get("villages", None)

        user_entry = {
            "name": name,
            "cell_phone": cell_phone,
            "region": input_region,
            "village": input_village
        }

        # only add if passed checking
        if check_user(user_entry):
            # add region number to phone number
            if user_entry["region"] == "United States":
                if not user_entry["cell_phone"].startswith("1"):
                    user_entry["cell_phone"] = "1" + str(user_entry["cell_phone"])
            elif user_entry["region"] == "Ethiopia":
                if not user_entry["cell_phone"].startswith("251"):
                    user_entry["cell_phone"] = "251" + str(user_entry["cell_phone"])
            else:
                print("Not supported")

            # add user to db
            add_user(user_entry)
        else:
            # did not fill all required fields
            print("could not add user.")

    # Get all of the current users, updated from the database
    user_list = get_all_users()
    call_list = get_call_logs()

    return render_template(
        "users.html", user_list=user_list, call_list=call_list,
        ethiopia_info=ethiopia_info)


@app.route("/send_call_route", methods=["POST", "GET"])
def send_call_route():

    # For doing actions to a list of people selected on our front end
    option = request.form["options"]
    selected = request.form.getlist("select", None)
    print (selected)
    if (option == "voice"):
        send_to_list(get_user_info_from_id_list(selected))
    elif (option == "delete"):
        users = get_user_info_from_id_list(selected)
        for user in users:
            delete_user(user)
    elif (option == "sms"):
        sms_text = request.form["question"]
        ethiopia_info['message'] = sms_text
        print (sms_text)
    else:
        print("This should not be reached.")

    '''
    Get all of the current users, updated from the database
    user_list = get_all_users()
    call_list = get_call_logs()
    '''

    # Check Status of call

    return redirect(url_for('users'))


def send_to_list(database_users):
    # TWO Important functions: Adds call to db & sends call
    for user_entry in database_users:
        call_id = send_call(user_entry['cell_phone'], user_entry['id'])
        add_call_to_db(user_entry['id'], call_id, None, None, False)


@app.route("/get_csv", methods=["POST"])
def foo():
    page = get_logs_csv()
    return redirect(page)


@app.route("/calls", methods=["GET", "POST"])
def calls():
    call_list = db_get_call_logs()
    return render_template("calls.html", call_list=call_list)

@app.route("/smssynch", methods=["GET", "POST"])
def synch():
    # http://ethiopia-sms.herokuapp.com/smssynch?task=send&secret=bschool
    task = request.args.get('task')
    # ts = datetime.datetime.now().strftime('+%Y-%m-%d %H:%M:%S UTC')
    ts = datetime.datetime.now()
    # ts = 'uniquesym'
    # print request.get_json()
    # time.sleep(300)
    if task == 'send':
      print ("send task")
      print (task)
      # print request.get_json()
      message = ethiopia_info.get('message')
      print (message)
      return '''{"payload": {
                  "success": "true",
                  "error": null,
                  "secret": "bschool",
                  "task": "send",
                  "messages": [{
                    "to": "+17149075336",
                    "message": "%s",
                    "uuid": "%s"}]
                  }
                  }''' % (message, str(ts))
    if task == 'sent':
      print ("sent task")
      print (task)
      print (request.get_json())
      messages_response = request.get_json()
      messages = messages_response.get('queued_messages')
      return '''{"message_uuids" : %s}''' % (messages)
    else:
      message = ethiopia_info.get('message')
      print ("print other task (should send msg to phone)")
      print (message)
      print (task)
      # print request.get_json()
      return '''{"payload": {
                  "success": "true",
                  "error": null,
                  "secret": "bschool",
                  "task": "send",
                  "messages": [{
                    "to": "+17149075336",
                    "message": "hello world",
                    "uuid": "%s"}]
                  }
                }''' % (str(ts))

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    ### Docs: http://twilio-python.readthedocs.org/en/latest/api/twiml.html#primary-verbs
    print ("we are calling: {}").format(request.args.get('caller'))
    caller_info = request.args.get('caller')
    question = request.args.get('question')
    response = twiml.Response()
    language="en"

    action = "/gather?caller={}&question={}".format(caller_info, question)
    question_info = get_questions()
    with response.gather(numDigits=1, action=action) as gather:
        # gather.play("http://ethiopia-sms.herokuapp.com/static/testsound.m4a")
        option = "Welcome. Did it rain yesterday? If yes, press 1. If no, press 2."
        question = question_info.get('init', option)
        gather.pause(length=5)

        gather.say(question, language=language, loop=2)

    return str(response)

@app.route('/gather', methods=['POST'])
def gather():
    caller_info = request.args.get('caller')
    question = request.args.get('question')
    digits = request.form['Digits'] #These are the inputted numbers
    language="en"
    response = twiml.Response()

    add_call_to_db(caller_info, None, question_info.get(question), digits, True)

    if digits == "1":
        action = "/gather?caller={}&question=1".format(caller_info)
        with response.gather(numDigits=1, action=action) as gather:
          option = "Thank you for telling us it rained. Has it rained for more than 3 days? Press 3 if it has, Press 0 if it has not."
          question = question_info.get('1', option)

          # add_call_to_db(caller_info, None, question, int(digits), True)
          gather.say(question, language=language, loop=1)

    elif digits == "2":
        action = "/gather?caller={}&question=2".format(caller_info)
        with response.gather(numDigits=1, action=action) as gather:
          option = "Thank you for telling us it did not rain."
          question = question_info.get('2', option)
          # add_call_to_db(caller_info, None, question, int(digits), True)
          response.say(question, language=language, loop=1)

    else:
        option = "Thank you for telling us it did rain. Goodbye."
        question = question_info.get('3', option)

        add_call_to_db(caller_info, None, question, None, True)
        response.say(option, language=language, loop=1)
    return str(response)

@app.route("/add_message", methods =["GET", "POST"])
def add_msg():

  if request.method == "POST":
    q_info = {}
    q_info['init'] = request.form.get('q1')
    q_info['1'] = request.form.get('q2')
    q_info['2'] = request.form.get('q3')
    q_info['3'] = request.form.get('q4')
    write_questions(q_info)

    global question_info
    question_info = get_questions()
    # if file and allowed_file(file.filename):
    #   filename = secure_filename(file.filename)
    #   file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #   return redirect(url_for('uploaded_file',
    #                           filename=filename))
  return render_template("record.html", question_info=question_info)

@app.route('/large.csv')
def generate_large_csv():
    csv = "'name','region','question','answer','timestamp','call_id'\n"
    call_list = db_get_call_logs()
    for call in call_list:
      if call['question']:
        q = str(call['question'].encode('utf-8')).replace(',', '')

        csv += "{},{},{},{},{},{}\n".format(call['name'],call['region'],q,call['answer'],call['timestamp'],call['call_id'])
      else:
        csv += "{},{},{},{},{},{}\n".format(call['name'],call['region'],call['question'],call['answer'],call['timestamp'],call['call_id'])


    response = make_response(csv)

    response.headers["Content-Disposition"] = "attachment; filename=calls.csv"

    return Response(csv, mimetype='text/csv')


#################
#
# The Following Routes are not used
#
#################

@app.route("/record_message", methods =["GET", "POST"])
def record():
  listofsounds = []
  if request.method == "POST":
    file = request.files['file']
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      return redirect(url_for('uploaded_file',
                              filename=filename))
  return render_template("record.html", listofsounds=listofsounds)

@app.route("/xml", methods=["GET", "POST"])
def return_xml():
  xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="en-US">Hello Welcome to Ethiopia SMS!</Say>
    <Gather action="/getdigits" timeout="5">
        <Say>Did it rain yesterday? Press 1 for Yes. Press 0 for No</Say>
    </Gather>
</Response>"""
  return Response(xml, mimetype='text/xml')

@app.route("/getdigits", methods=["GET", "POST"])
def get_digits():
  digits = request.args.get('Digits')
  json = request.get_json()
  print (digits)
  print (json)

  xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="en-US">You Entered {} For the Questions We asked</Say>
</Response>""".format(digits)
  return Response(xml, mimetype='text/xml')

