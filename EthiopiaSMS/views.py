from EthiopiaSMS import app
from flask import render_template, request, redirect, url_for, Response, make_response
from flask.ext.basicauth import BasicAuth
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
import glob

user_list = None
call_list = None
ethiopia_info = {
    "regions": ["Santo Domingo", "Puerto Plata"],
    "villages": [],
    "message": ""
}


def write_questions(questions):

  q_info = questions
  if questions['1']:
    update_question(q_info['1'], 1,"es")

  if questions['1']:
    update_question(q_info['2'], 2,"es")

  if questions['2']:
    update_question(q_info['3'], 3,"es")

  if questions['3']:
     update_question(q_info['4'], 4,"es")



def get_questions():
  q_data = load_questions()
  # with open(os.path.join(APP_STATIC,'questions.json')) as f:
  #   q_data = json.load(f)

  return q_data


question_info = get_questions()


app.config['BASIC_AUTH_USERNAME'] = AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = AUTH_PASSWORD

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/recordings')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

basic_auth = BasicAuth(app)

def get_sounds():
  baseurl = "http://ethiopia-sms.herokuapp.com/"
  final_soundlist = []
  types = ('/*.mp3', '/*.m4a')
  full_filenames = []
  full_filenames = glob.glob(UPLOAD_FOLDER + "/*.mp3")
  # for file in types:
  #   full_filenames.extend(glob.glob(UPLOAD_FOLDER + file))
  print full_filenames
  for full_thing in full_filenames:
    filename = full_thing.split("/")[-1]
    final_soundlist.append(baseurl + "static/recordings/" + filename)

  return final_soundlist

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
@basic_auth.required
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
        cell_phone_list = []
        name = request.form.get("name", None)
        input_region = request.form.get("regions", None)
        input_village = request.form.get("villages", None)

        if "," in cell_phone:
          cell_phone_list = cell_phone.split(",")

          for n in cell_phone_list:
            user_entry = {
              "name": name,
              "cell_phone": n,
              "region": input_region,
              "village": input_village
            }
            add_user(user_entry)

        else:
          user_entry = {
              "name": name,
              "cell_phone": cell_phone,
              "region": input_region,
              "village": input_village
          }
          if (check_user(user_entry)):
            add_user(user_entry)

        # # only add if passed checking
        # if check_user(user_entry):
        #     # add region number to phone number
        #     if user_entry["region"] == "United States":
        #         if not user_entry["cell_phone"].startswith("1"):
        #             user_entry["cell_phone"] = "1" + str(user_entry["cell_phone"])
        #     elif user_entry["region"] == "Ethiopia":
        #         if not user_entry["cell_phone"].startswith("251"):
        #             user_entry["cell_phone"] = "251" + str(user_entry["cell_phone"])
        #     else:
        #         print("Not supported")

        #     # add user to db
        #     add_user(user_entry)
        # else:
        #     # did not fill all required fields
        #     print("could not add user.")

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
        add_call_to_db(user_entry['id'], call_id, "Call Initiated", None, False)


@app.route("/get_csv", methods=["POST"])
def foo():
    page = get_logs_csv()
    return redirect(page)


@app.route("/calls", methods=["GET", "POST"])
@basic_auth.required
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

@app.route('/ivr/welcome', methods=['POST', 'GET'])
def welcome():
  caller_info = request.args.get('caller')
  question_info = get_questions()
  question = question_info.get('1')

  response = twiml.Response()

  ### IVR Phone Tree: https://www.twilio.com/docs/tutorials/walkthrough/ivr-phone-tree/python/flask#7
  ### Advanced: https://www.twilio.com/blog/2014/06/building-better-phone-trees-with-twilio.html
  with response.gather(numDigits=1, action=url_for('menu', caller=caller_info, question=1), method="POST") as g:
    g.play(url=question, loop=2)
    return str(response)


@app.route('/ivr/menu', methods=['POST', 'GET'])
def menu():
  caller_info = request.args.get('caller')
  selected_option = request.form['Digits']
  question_info = get_questions()

  option_actions = {
    "1": _get_hours_rained,
    "2": _get_not_rained
  }

  if option_actions.has_key(selected_option):
    response = twiml.Response()
    option_actions[selected_option](response, question_info, caller_info)
    return str(response)
  else:
    return redirect(url_for('welcome', caller=caller_info))

@app.route('/ivr/hours_of_rain', methods=['POST', 'GET'])
def hours_rained():
  selected_option = 0

  if request.form['Digits']:
    selected_option = request.form['Digits']
  caller_info = request.args.get('caller')

  add_call_to_db(caller_info, None, 'How many hours did it rain?', selected_option, True)

  response = twiml.Response()
  question_info = get_questions()

  response.play(question_info.get('3'))
  response.hangup()
  return str(response)

def _get_hours_rained(response, question_info, caller_info):
  add_call_to_db(caller_info, None, 'Did it rain?', 1, True)

  with response.gather(numDigits=1, action=url_for('hours_rained', caller=caller_info, question=2), method="POST") as g:
    g.play(question_info.get('2'), loop=2)
    return str(response)

def _get_not_rained(response, question_info, caller_info):
  add_call_to_db(caller_info, None, 'Did it Rain?', 0, True)

  response.play(question_info.get('4'))
  response.hangup()
  return str(response)

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    ### Docs: http://twilio-python.readthedocs.org/en/latest/api/twiml.html#primary-verbs
    print ("we are calling: {}").format(request.args.get('caller'))
    caller_info = request.args.get('caller')
    question = request.args.get('question')
    response = twiml.Response()
    language="es"

    action = "/gather?caller={}&question=1".format(caller_info)
    question_info = get_questions()

    with response.gather(numDigits=1, action=action) as gather:
        # gather.play("http://ethiopia-sms.herokuapp.com/static/testsound.m4a")
        option = "Error"
        question = question_info.get('1', option)
        gather.pause(length=1)
        gather.play(question, loop=2)

        # gather.say(question, language=language, loop=3)

    return str(response)

@app.route('/gather', methods=['POST'])
def gather():
    caller_info = request.args.get('caller')
    question = request.args.get('question')
    if request.form['Digits']:
      digits = request.form['Digits'] #These are the inputted numbers
    language="es"
    response = twiml.Response()

    print "Current questions: "
    print question_info

    add_call_to_db(caller_info, None, question_info.get(question), digits, True)

    if digits == "1":
        action = "/gather?caller={}&question=2".format(caller_info)
        with response.gather(numDigits=1, action=action) as gather:
          option = "Error"
          question = question_info.get('2', option)

          # add_call_to_db(caller_info, None, question, int(digits), True)
          gather.play(question, loop=2)
          # gather.say(question, language=language, loop=1)

    elif digits == "2":
        action = "/gather?caller={}&question=3".format(caller_info)
        with response.gather(numDigits=1, action=action) as gather:
          option = "Error"
          question = question_info.get('3', option)
          # add_call_to_db(caller_info, None, question, int(digits), True)
          response.play(question, loop=1)
          # response.say(question, language=language, loop=1)

    else:
        option = "Error"
        question = question_info.get('4', option)

        add_call_to_db(caller_info, None, question, 0, True)
        response.play(question, loop=1)
        # response.say(option, language=language, loop=1)
    return str(response)

@app.route("/upload_sound", methods=["GET", "POST"])
def upload_sound():
  # maybe check for accepted audio stuff https://www.twilio.com/docs/api/rest/accepted-mime-types#accepted
  if request.method == 'POST':
        print "got here"
        # check if the post request has the file part
        if 'file' not in request.files:
            print "no file here"
            return redirect(request.url)

        file = request.files['file']
        print file.filename
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print "also dumb"
            return redirect(request.url)
        if file:
            print "this is when it works"
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('add_msg'))
  return redirect(url_for('add_msg'))

@app.route("/add_message", methods =["GET", "POST"])
@basic_auth.required
def add_msg():

  if request.method == "POST":
    q_info = {}
    q_info['1'] = request.form.get('q1')
    q_info['2'] = request.form.get('q2')
    q_info['3'] = request.form.get('q3')
    q_info['4'] = request.form.get('q4')
    print "we got something"
    print q_info

    write_questions(q_info)

  global question_info
  question_info = get_questions()

  soundlist = get_sounds()
  print soundlist
  # if file and allowed_file(file.filename):
  #   filename = secure_filename(file.filename)
  #   file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
  #   return redirect(url_for('uploaded_file',
  #                           filename=filename))
  return render_template("record.html", question_info=question_info, soundlist=soundlist)

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

