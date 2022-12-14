#!/usr/bin/env python3

import sys
import os
import subprocess
import re
import logging
import time
from flask import jsonify, request, Flask, render_template, Response, send_from_directory
from OpenSSL import SSL
import ssl
import datetime

lastaction = "none"
reponame = "Please Register an application"
gitrepo = "Please Register an application"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', utc_dt=datetime.datetime.utcnow())

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/buildserver/')
def buildserver():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/files/'
    return send_from_directory(filepath, 'build-server.pdf')

@app.route('/hello/')
def hello():
    return render_template('hello.html')

@app.route('/register/')
def register():
    return render_template('register.html')

@app.route('/register/',methods=['POST'])
def register_post():
    global reponame
    global gitrepo
    reponame = request.form['text']
    gitrepo = "git@github.com:razrman/" + reponame + ".git"
    cmd="cd ../workspace && git clone " + gitrepo
    try:
        command = subprocess.check_call(cmd,shell=True)
        return gitrepo + " cloned"
    except:
        cmd = "cd ../workspace/" + reponame + " && git pull "
        try:
            command = subprocess.check_call(cmd,shell=True)
            return gitrepo + " pulled"
        except:
            return gitrepo + " Not found"

@app.route("/build/")
def build():
    return render_template(
            'build.html',
            command_list=[{'name':'build'},{'name':'test'},{'name':'clean'},{'name':'deploy'}],
            app_name=reponame)

@app.route("/gitlab/",methods=['POST'])
def gitlab():
    app.logger.info(request.get_json())
    return "Message Received"

@app.route("/douild/" , methods=['GET', 'POST'])
def dobuild():
    global lastaction
    global gitrepo
    global reponame
    action = request.form['submit_button']
    logfile = "../log/" + reponame + "-"+action+".out"
    if "Please" in reponame:
        return reponame
    if str(action) == 'build':
        cmd = "cd ../workspace/" + reponame + " && make "
        execute(cmd,logfile)
        #command = subprocess.check_call(cmd,shell=True)
        lastaction="build"
        return gitrepo + " " + cmd
    elif str(action) == 'clean':
        cmd = "cd ../workspace/" + reponame + " && make clean"
        execute(cmd,logfile)
        #command = subprocess.check_call(cmd,shell=True)
        lastaction="clean"
        return gitrepo + " " + cmd
    elif str(action) == 'test':
        cmd = "cd ../workspace/" + reponame + " && make test"
        lastaction="test"
        try:
            # command = subprocess.check_call(cmd,shell=True)
            execute(cmd,logfile)
            return gitrepo + " " + cmd
        except:
            return gitrepo + " Makefile does not have a test step"
    elif str(action) == 'deploy':
        cmd = "cd ../workspace/" + reponame + " && echo 'Deploying' " + reponame
        command = subprocess.check_call(cmd,shell=True)
        lastaction="deploy"
        return gitrepo + " " + cmd
    elif str(action) == 'status':
        filename = "../log/" + reponame + "-"+lastaction+".out"
        if os.path.exists(filename):
            cmd="cat " + filename
            command = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE)
            logoutput=command.stdout.decode('ascii')
            r = Response(logoutput.replace('\n','<br>'))
            return r
        else:
            return "Log file "+filename+" does not exist"
    else:
        return " ERROR: " + gitrepo + " Build Action " + action + " Incorrect"

def execute(command,logfile):

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        with open(logfile, 'w') as f:
            print(logfile,file=f)
            print(output.decode(),file=f)
    else:
        raise ProcessException(command, exitCode, output)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8080',debug=True)
