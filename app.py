###########################  IMPORT NECESSARY MODULES  ####################

from flask import Flask, request, render_template,redirect, url_for
from werkzeug.utils import secure_filename
import os
from os import listdir
import json
from datetime import datetime
import face_recognition as fr
import numpy as np
import csv
import re
import pdb

############################################################################

UPLOAD_FOLDER = 'received_files'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']

###########  IMPORT FACE ENCODINGS  #######################################################################
faces = np.load('enc/encodings.npy',allow_pickle = True) #### LOADING    ENCODING OBJECT       ############
encodings = faces.item()                                 #### this is    ENCODING DICTIONARY  #############
recent_encodings = []
###########################################################################################################
#########################  CLEANING ATTENDANCE FILE #######################################################
with open('attendance/attn.csv', 'w') as writeFile:
    writer = csv.writer(writeFile)
    writer.writerow([])
###########################################################################################################

attend = {}          ##  DICTIONARY TO STORE DYNAMIC ATTENDANCE ##################################


#######################################  COMPARING FACE ENCODINGS #########################################
def face_rec(file):
    img = fr.load_image_file(file)           
    img_enc = fr.face_encodings(img)[0] ###  stores encoding of imported file
    recent_encodings.append(img_enc)    ###  global variable to use later

    for name in encodings:  ### iterate through encodings dictionary

        time = datetime.now()
        time = time.strftime('%X')   ## time in string format for attendance
        results = fr.compare_faces([encodings.get(name)], img_enc,tolerance = 0.5)
        print(name,results)

        if results == [True]:  ### if all array values match
            #print('matched with '+ name)
            for key in attend:                      ### check if attendance is already taken
                if key == name:
                    return "Attendance taken"
            attend[name] = time      ### value of dictionary attend[name] is the current time
            print(attend)
            with open('attendance/attn.csv', 'w') as writeFile:   ### write attendance in csv file to read 
                writer = csv.writer(writeFile)
                for x,y in attend.items():
                    writer.writerow([x,y])
                return name

    return 'Unknown'
#########################################################################################################


################################# CHECKING IF IT IS AN IMAGE FILE  ######################################
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
########################################################################################################

################################# FILE CHECK ###########################################################
def print_request(request):
    # Print request url
    print(request.url)
    # print relative headers
    print('content-type: "%s"' % request.headers.get('content-type'))
    print('content-length: %s' % request.headers.get('content-length'))
    # print body content
    body_bytes=request.get_data()
    # replace image raw data with string '<image raw data>'
    body_sub_image_data=re.sub(b'(\r\n\r\n)(.*?)(\r\n--)',br'\1<image raw data>\3', body_bytes,flags=re.DOTALL)
    print(body_sub_image_data.decode('utf-8'))

##########################################################################################################



app = Flask(__name__)

############################## ROUTE TO MARK ATTENDANCE OF NEW FACES AND UPDATE THEIR ENCODING  ##########

@app.route('/add',methods = ['GET','POST'])
def add_name():
    if request.method == 'GET':
        return render_template('adder.html')
    n = str(request.form['fname'])
    e = recent_encodings[-1]
    encodings[n] = e
    time = datetime.now()
    time = time.strftime('%X')
    attend[n] = time
    with open('attendance/attn.csv', 'w') as writeFile:
        writer = csv.writer(writeFile)
        for x,y in attend.items():
            writer.writerow([x,y])

    np.save('enc/encodings', encodings)  ################  SAVING ENCODING OF NEW FACE  ##############

    return'''
<!doctype html>
    <title>Face Recognition</title>
    <h1>Updated</h1>
    <form action = '/' method = 'get'>
      <input type=submit value=Check status>
    </form>
    '''
#############################################################################################################







######################################## HOME PAGE/ DASHBOARD ###############################################
@app.route('/',methods = ['GET','POST'])
def attendance():
    if request.method == 'GET':
        dic = {}
        with open('attendance/attn.csv','r') as file:
            rows = csv.reader(file)
            for row in rows:
                if len(row) != 0:
                    dic[row[0]] = row[1]
        return render_template('hom.html',dicts = dic)
                
############################################################################

@app.route('/face_rec', methods=['POST', 'GET'])
def face_recognition():
    if request.method == 'POST':
        # Print request url, headers and content
        print_request(request)

        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files.get('file')
        # if user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)

        if allowed_file(file.filename):
            name = face_rec(file)
            if name == 'Unknown':
                return render_template('adder.html')

            return '''
    <!doctype html>
    <title>Face Recognition</title>
    <h1>Updated</h1>
    <form action = '/' method = 'get'>
      <input type=submit value=Check status>
    </form>
    '''

    return '''
    <!doctype html>
    <title>Face Recognition</title>
    <h1>Upload an image</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''





if __name__ == '__main__':      ## runs the app in debug mode
    app.run(debug=True)


#img = fr.load_image_file('static/khirod.png')
#enc = fr.face_encodings(img)[0]

#for name in encodings:
#   if (encodings.get(name) == enc).all():
#       print('matched with '+name)