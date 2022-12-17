from flask import Flask

#UPLOAD_FOLDER = '/Users/phyllisfrankl/Documents/Magic\ Briefcase/CS3083\ Spring\ 2020/FlaskDemoSpr2020/FlaskDemoPhotos'
UPLOAD_FOLDER = 'FlaskDemoPhotos'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
