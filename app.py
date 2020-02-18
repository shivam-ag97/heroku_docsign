import time
from io import BytesIO
from PIL import Image
from flask import Flask, jsonify, request, render_template, g, url_for, session, redirect, send_file, flash, abort, \
    jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_restful import Api, Resource
from pymongo import MongoClient
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
import os
import glob
from binascii import a2b_base64
import random
import string

UPLOAD_FOLDER = "images"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
api = Api(app)
app.secret_key = 'qweasb@#12344'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = MongoClient('mongodb+srv://shivam:shivam@cluster0-3mbds.mongodb.net/test?retryWrites=true&w=majority')
db = client.get_database('docsign')
users = db.users


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/sign_one_page',methods=['POST','GET'])
def sign_one_page():
    user=session['_id_']
    sign_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    input_path="images/" + user + '_to_sign_' + ".pdf"
    watermark = PdfFileReader(open(sign_path, "rb"))
    input_file = PdfFileReader(open(input_path, "rb"))
    output_file = PdfFileWriter()
    page_count=input_file.getNumPages()
    input_page = input_file.getPage(0)
    input_page.mergePage(watermark.getPage(0))
    output_file.addPage(input_page)
    for page_number in range(1,page_count):
        input_page = input_file.getPage(page_number)
        output_file.addPage(input_page)
    output_path="final_pdf/" + user + '_signed_' + '.pdf'
    with open(output_path, "wb") as outputStream:
            output_file.write(outputStream)
    return send_file("final_pdf/" + user + '_signed_' + '.pdf',as_attachment=True)

@app.route('/sign_all')
def sign_all():
    user=session['_id_']
    sign_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    input_path="images/" + user + '_to_sign_' + ".pdf"
    watermark = PdfFileReader(open(sign_path, "rb"))
    input_file = PdfFileReader(open(input_path, "rb"))
    output_file = PdfFileWriter()
    page_count=input_file.getNumPages()
    for page_number in range(page_count):
        input_page = input_file.getPage(page_number)
        input_page.mergePage(watermark.getPage(0))
        output_file.addPage(input_page)
    output_path="final_pdf/" + user + '_signed_' + '.pdf'
    with open(output_path, "wb") as outputStream:
            output_file.write(outputStream)
    return send_file("final_pdf/" + user + '_signed_' + '.pdf',as_attachment=True)   



@app.route('/generate_pdf', methods=['POST','GET'])
def gen_pdf_from_sign():
    user=session['_id_']
    picture_path="images/" + user + '_sign_' + ".png"
    temp_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    # c = canvas.Canvas('D:/uploads/temp.pdf')
    c=canvas.Canvas(temp_path)
    x=request.form['x']
    y=request.form['y']
    c.drawImage(picture_path, int(x), int(y), width=180, height=80, mask='auto')
    c.save()
    # sign_one_page()
    # sign_path = '~/Downloads/uploads/temp.pdf'
    # input_path = '~/Downloads/uploads/' + session['user'] + '.pdf'
    # sign_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    # input_path="images/" + user + '_to_sign_' + ".pdf"
    # watermark = PdfFileReader(open(sign_path, "rb"))
    # input_file = PdfFileReader(open(input_path, "rb"))
    # output_file = PdfFileWriter()
    # input_page = input_file.getPage(0)
    # input_page.mergePage(watermark.getPage(0))
    # output_file.addPage(input_page)
    # # folder_path = 'D:/uploads/'
    # # output_path = folder_path + 'signed' + '.pdf'
    # output_path="final_pdf/" + user + '_signed_' + '.pdf'
    # with open(output_path, "wb") as outputStream:
    #     output_file.write(outputStream)
    return render_template("test.html")







@app.route('/return')
def return_files():
    try:
        # user=session['user']
        user=session['_id_']
        # filepath='final_pdf/' + user + '_signed_' + ".pdf"
        return send_file("final_pdf/" + user + '_signed_' + '.pdf',as_attachment=True)
        # return send_file('~/Downloads/signed.pdf', as_attachment=True)
    except Exception as e:
        return str(e)


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))



@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        session.pop('_id', None)
        users = db.users
        login_user = users.find_one({'user_id': request.form['user']})
        if login_user:
            p = request.form['password']
            if p == login_user['pw']:
                session['user'] = login_user['user_id']
                user = login_user['user_name']
                session['_id_']=randomString(8)
                # user = {'username': user}
                return redirect(url_for('protected'))
                # id=session['_id_']
                # return jsonify(id);
            return "Invalid userID or password"
        return "Invalid Credentials"
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'user_id': request.form['userid']})

        if existing_user is None:
            users.insert(
                {'user_id': request.form['userid'], 'pw': request.form['pass'], 'user_name': request.form['username']})
            session['user_name'] = request.form['username']
            return redirect(url_for('index'))

        return " User already registered! "
    return render_template('register.html')


@app.route('/protected')
def protected():
    if g.user:
        return render_template('upload.html',user=session['user'])
        # return render_template('draw.html', user=session['user'])
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None
    g._id_ =    None

    if 'user' in session:
        g.user = session['user']
        g._id_ = session['_id_']


@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    session.pop('_id_', None)
    return render_template('index.html')


@app.route('/upload')
def upload_form():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            # filename = session['user']+'_to_sign_' + ".pdf"
            f=file.filename
            # f=f[:-4].strip().replace(" ","_").upper()
            # return jsonify(f)
            filename = session['_id_']+'_to_sign_' + ".pdf"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            # return redirect('/upload')
            return render_template('draw.html')
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(request.url)


@app.route('/upload-sign', methods=['POST'])
def uploadsign():
    # user = session['user']
    user = session['_id_']
    data = request.json
    base64String = data['image'].replace("data:image/png;base64,", "")
    binary_data = a2b_base64(base64String)
    seconds = str(time.time())
    # filaname = "images/" + user + '_sign_' + seconds + ".png"
    filaname="images/" + user + '_sign_' + ".png"
    fd = open(filaname, 'wb')
    fd.write(binary_data)
    fd.close()
    # gen_pdf_from_sign()
    # return_files()
    # return render_template('upload.html')
    return jsonify(data=filaname, message="uploaded")



@app.route('/position')
def pos():
    return render_template('pos.html')


if __name__ == "__main__":
    app.run(debug=True)
