#!/usr/bin/env python3

import sys
import os
import subprocess
import re
import logging
import time
from flask import jsonify, request, Flask, render_template, Response
from OpenSSL import SSL
import ssl
import datetime

# syslist = ["idq-datahive.pnmac.com", "pcg-datahive.pnmac.com", "edc-datahive.pnmac.com", "datahive.pnmac.com"]
syslist = ["idq-datahive-dev.pnmac.com", "pcg-datahive-dev.pnmac.com", "edc-datahive-dev.pnmac.com", "datahive-dev.pnmac.com"]
lastaction = "none"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', utc_dt=datetime.datetime.utcnow())

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/hello/')
def hello():
    return render_template('hello.html')

@app.route('/register/')
def register():
    return render_template('register.html')

@app.route('/register/',methods=['POST'])
def register_post():
    text = request.form['text']
    processed_text = text.upper()
    return processed_text

@app.route("/build/")
def build():
    return render_template(
            'build.html',
            command_list=[{'name':'build'},{'name':'test'},{'name':'clean'},{'name':'deploy'}])

@app.route("/gitlab/",methods=['POST'])
def gitlab():
    app.logger.info(request.get_json())
    return "Message Received"

@app.route("/dobuild/", methods=['GET','POST'])
def dobuild():
    command = request.form['command_select']
    return "Running command " + command

@app.route("/dorecycle/" , methods=['GET', 'POST'])
def dorecycle():
    system = request.form['server_select']
    action = request.form['submit_button']
    if str(action) == 'recycle':
        cmd=["ssh", "infa@" + system, "/home/infa/recycleinfa.sh"]
        with open("/tmp/"+system+"-recycle.out","w") as out:
            command = subprocess.Popen(cmd,stdout=out,stderr=out)
        return(system+" RECYCLING! ")
    elif str(action) == 'checklog':
        filename = "/tmp/" + system + "-recycle.out"
        if os.path.exists(filename):
            cmd="cat " + filename
            command = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE)
            logoutput=command.stdout.decode('ascii')
            r = Response(logoutput.replace('\n','<br>'))
            return r
        else:
            return "Log file "+filename+" does not exist"
    else:
        return " ERROR: " + system + " RECYCLE Incorrect, Please include Correct Parameters to recycle"

@app.route("/doaxon/" , methods=['GET', 'POST'])
def doaxon():
    global lastaction
    system = request.form['server_select']
    action = request.form['submit_button']
    if str(action) == 'stopinfa':
        cmd=["ssh", "infa@" + system, "/home/infa/stopinfa.sh"]
        with open("/tmp/"+system+"-stopinfa.out","w") as out:
            command = subprocess.Popen(cmd,stdout=out,stderr=out)
        lastaction="stopinfa"
        return(system+" STOPPING! ")
    elif str(action) == 'startinfa':
        cmd=["ssh", "infa@" + system, "/home/infa/startinfa.sh"]
        with open("/tmp/"+system+"-stopinfa.out","w") as out:
            command = subprocess.Popen(cmd,stdout=out,stderr=out)
        lastaction="startinfa"
        return(system+" STARTING! ")
    elif str(action) == 'paramsync':
        cmd=["ssh", "infa@" + system, "/home/infa/paramsync.sh"]
        with open("/tmp/"+system+"-paramsync.out","w") as out:
            command = subprocess.Popen(cmd,stdout=out,stderr=out)
        lastaction="paramsync"
        return(system+" PARAMSYNC! ")
    elif str(action) == 'checklog':
        filename = "/tmp/" + system + "-"+lastaction+".out"
        if os.path.exists(filename):
            cmd="cat " + filename
            command = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE)
            logoutput=command.stdout.decode('ascii')
            r = Response(logoutput.replace('\n','<br>'))
            return r
        else:
            return "Log file "+filename+" does not exist"
    else:
        return " ERROR: " + system + " RECYCLE Incorrect, Please include Correct Parameters to recycle"

@app.route('/recycleinfa', methods=['GET'])
def recycleinfa():
    application=""
    system=""
    if ('Application_Name' in request.args) and ('System_Name' in request.args):
        application=request.args['Application_Name']
        system=request.args['System_Name']
    if application == "recycleinfa" and system in syslist:
        cmd=["ssh", "infa@" + system, "/home/infa/recycleinfa.sh"]
        with open("/tmp/"+system+"-"+application+".out","w") as out, open("/tmp/"+system+"-"+application+".err","w") as err:
            command = subprocess.Popen(cmd,stdout=out,stderr=err)
        return system + " " + application + " Started"
    else:
        return " ERROR: " + system + "," + application + " Incorrect, Please include Correct Parameters to recycle"

@app.route('/axoncommand', methods=['GET'])
def axoncommand():
    application=""
    system=""
    if ('Application_Name' in request.args) and ('System_Name' in request.args):
        application=request.args['Application_Name']
        system=request.args['System_Name']
    if application in ["startup", "shutdown", "paramsync"]  and system == "datahive-dev.pnmac.com":
        if application == "paramsync":
            cmd=["ssh", "infa@" + system, "/opt/Informatica/Axon7.2.0/axonhome/third-party-app/scripts/paramsync"]
        else:
            cmd=["ssh", "infa@" + system, "/opt/Informatica/Axon7.2.0/bin/" + application +".sh"]
        with open("/tmp/"+system+"-"+application+".out","w") as out:
            command = subprocess.Popen(cmd,stdout=out,stderr=out)
        return system + " " + application + " Started"
    else:
        return " ERROR: " + system + "," + application + " Incorrect, Please include Correct Parameters for Axoni Command"

@app.route('/checkoutput', methods=['GET'])
def checkoutput():
    application=""
    system=""
    if ('Application_Name' in request.args) and ('System_Name' in request.args):
        application=request.args['Application_Name']
        system=request.args['System_Name']
    if application in ["recycleinfa","stopinfa","startinfa", "paramsync"] and system in syslist:
        filename = "/tmp/" + system + "-" + application 
        if os.path.getsize(filename + ".out") != 0:
            cmd="cat " + filename + ".out"
        command = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE)
        return command.stdout.decode('ascii')
    else:
        return " ERROR: " + system + "," + application + " Incorrect, Please include Correct Parameters to check recycle"

@app.route('/run_mapping', methods=['GET'])
def run_mapping():
    domain ="PNMAC_IDQ_DEV"
    service="IDQ_DIS_DEV"
    system ="idq-datahive-dev.pnmac.com"
    adminpw="AdminPasswordHere"
    if ('Application_Name' in request.args) and ('Workflow_Name' in request.args):
        application=request.args['Application_Name']
        workflow=request.args['Workflow_Name']
        cmd="ssh infa@"+system+" infacmd.sh wfs startworkflow -dn "+domain+" -un Administrator -pd "+adminpw+" -sn "+service+" -a "+application+" -wf "+workflow
        command = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE)
        print(command.stdout)
        return command.stdout

if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8080',debug=True)
