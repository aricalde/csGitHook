#Copyright (c) 2013 Cluster Studio S.C.
#-------------------------------------------------------
#:author: Rodrigo Rodriguez
#:organization: Cluster Studio S.C.
#:contact: rodrigorn@clusterstudio.com

import sh
import logging
import traceback

from flask import Flask, request, json
from logging import Formatter
from logging.handlers import SMTPHandler, RotatingFileHandler

from shotgun_api3.shotgun import Shotgun

SERVER_PATH = 'YOUR_SHOTGUN_SERVER_URL'
SCRIPT_USER = 'YOUR_SHOTGUN_SCRIPT_USER'
SCRIPT_KEY =  'YOUR_SHOTGUN_SCRIPT_KEY'

sg = Shotgun(SERVER_PATH, SCRIPT_USER, SCRIPT_KEY)

app = Flask(__name__)

# Setup email handler
mail_handler = SMTPHandler() # Use your own settings here
mail_handler.setFormatter(Formatter("""
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
    """))
mail_handler.setLevel(logging.ERROR)
app.logger.addHandler(mail_handler)

# Setup file handler
file_handler = RotatingFileHandler() # Use your own settings here
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(module)s]'
))
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

@app.route('/some/path/out/in/the/wild', methods = ['POST']) # Use your own path here
def on_push():
    try:
        # Get commit info
        payload = request.form.get('payload')
        payload_dict = json.loads(payload)
        repo_name = payload_dict['repository']['name']
        app.logger.info("Repository name: %s" % repo_name)

        # Get tool info
        tool = sg.find_one('Tool',
            [['sg_repo_1', 'is', repo_name]],
            ['code', 'sg_bitbucket', 'sg_local_path'])
        if not tool:
            raise Exception("No Tool for repo: %s" % repo_name)
        if not tool['sg_local_path']:
            raise Exception("No path for Tool: %s" % tool['code'])
        tool_path = tool['sg_local_path']['local_path']
        app.logger.info("Repository path: %s" % tool_path)

        # Do pull
        git = sh.git.bake(_cwd=tool_path)
        git.reset(hard= True)
        git.pull()

    except:
        app.logger.error("\n\nPayLoad:\n\n%s\n\nTraceback:\n\n%s\n" % (repr(payload_dict),traceback.format_exc()))
        return '', 500

    return '', 200

if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug = True, port= 80)
