# This is a basic web site partially modified from https://www.youtube.com/watch?v=Z1RJmh_OqeA
# To execute this file,
#   1. install python3 (verify with "$python3 --version")
#   2. install pip3 (verify with "$pip3 --version")
#   3. install virtualenv (issue "$pip3 install virtualenv")
#   4. From VisualStudio Code, go to View -> Command Pallete -> Choose "Python: Select Interpreter" -> Choose the one in ./env/bin/python
#   5. go to your folder with the files for this app
#   6. Create virtual environment (issue "$virtualenv env")
#   7. Activate the virtual environment (issue "$source env/bin/activate")
#   8. Install flask and other related packages (issue "$pip3 install flask boto3 flask-mysql <name_of_package>")
#   9. Move this file to the folder
#   10. Exceute this file (issue "$ python3 <filename>")

# To create DB locally using SQLAlchemy
#   1. Go to python3 (issue "$python3")
#   2. ">>> from app import db"
#   3. ">>> db.create_all()"
#   5. ">>> exit()"

# To deploy flask app to Lambda via Zappa
#   1. install zappa package ("issue $pip3 install zappa")
#   2. create zappa setting file ("issue $zappa init")
#   3. create requirements.txt file using pip freeze (issue "$pip3 freeze > requirements.txt")
#   4. deploy on AWS (issue "$zappa deploy dev")
#       optionally, redeploy on AWS (issue "$zappa update dev")
#   5. to shutdown and delete the app (issue "$zappa undeploy dev")

from flask import Flask, jsonify, render_template, url_for, request, redirect, jsonify, flash
from flaskext.mysql import MySQL
#from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import boto3, uuid, json

app = Flask(__name__)
app.secret_key = "myownsecret"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

# This "/home/ec2-user/dbserver.endpoint" file has to be created from cloudformation template and it has RDS endpoint
db_endpoint = open("/home/ec2-user/dbserver.endpoint", 'r', encoding='UTF-8')


# Configure mysql database
app.config['MYSQL_DATABASE_HOST'] = db_endpoint.readline().strip()
app.config['MYSQL_DATABASE_USER'] = 'admin'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Enes123456'
app.config['MYSQL_DATABASE_DB'] = 'enes_phonebook'
app.config['MYSQL_DATABASE_PORT'] = 3306

mysql = MySQL()
mysql.init_app(app)
connection = mysql.connect()
connection.autocommit(True)
cursor = connection.cursor()

client = boto3.client('frauddetector', region_name='us-east-1')

class Claimant():
    name = ''
    ua = ''
    ip = ''
    address = ''
    state = ''
    postal = ''
    phone = ''
    email = ''

    def __repr__(self):
        return '<Task %r>' % self.name

@app.route('/', methods=['GET', 'POST']) 
def index():
    if request.method == 'POST':
        thisUser = Claimant()

        thisUser.name = request.form['inputName']
        thisUser.ua = request.form['inputUserAgent']
        thisUser.ip = request.form['inputIP']
        thisUser.address = request.form['inputAddress'] + ' ' + request.form['inputCity']
        thisUser.state = request.form['inputState']
        thisUser.postal = request.form['inputZip']
        thisUser.phone = request.form["inputPhone"]
        thisUser.email = request.form['inputEmail'] 

        try:
            print(thisUser.name)

            try:
                response = client.get_event_prediction(
                    detectorId="detector-getting-started",
                    eventId=str(uuid.uuid4()),
                    eventTypeName="registration",
                    eventTimestamp="2019-08-10T20:44:00Z",
                    entities=[{"entityType": "customer", "entityId": str(uuid.uuid4())},],
                    eventVariables={
                        "email_address": thisUser.email,
                        "ip_address": "46.41.252.160"
                    }
                )
                outcome = json.dumps(response['ruleResults'][0]['outcomes'][0])[1:-1]
            except:
                outcome = "N/A"

            print('Response: {}'.format(outcome))

            # query = '''INSERT INTO phonebook (name) VALUES ("{}")'''.format(thisUser.name)
            # query = 'SELECT count(*) FROM phonebook'
            query = '''
                        INSERT INTO phonebook 
                        (name, number, ip_address, email_address, billing_state, user_agent, billing_postal, billing_address) 
                        VALUES("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")
                    '''.format(thisUser.name, thisUser.phone, thisUser.ip, thisUser.email, thisUser.state, thisUser.ua, thisUser.postal, thisUser.address)
            print(query)
            cursor.execute(query)
            output = cursor.fetchone()
            print(output)
            # cursor.execute('''INSERT
            #                 INTO phonebook 
            #                 (name, number, ip_address, email_address, billing_state, user_agent, billing_postal, billing_address) 
            #                 VALUES("{}", "{}", {}, {}, {}, {}, {}, {})'''.format(thisUser.name, thisUser.phone, thisUser.ip, thisUser.email, thisUser.state, thisUser.ua, thisUser.postal, thisUser.address))
            flash(f"New claim for {thisUser.name} has been recorded: {outcome}")
            return redirect('/')
        except:
            return 'There was an issue adding your task'
        return redirect('/')
    else:
        return render_template('form.html')

if __name__ == "__main__":
    #app.run(debug = True)
    app.run(host='0.0.0.0', port=80)
