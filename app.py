from datetime import *

from flask import *
from pymongo import MongoClient
from bs4 import BeautifulSoup
from flask_jwt_extended import *
from flask_bcrypt import *

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "secret"
jwt = JWTManager(app)

client = MongoClient('localhost', 27017)
db = client.dbArticle

@app.route('/', methods = ['GET'])
def home():
    return render_template('login.html')

@app.route('/login', methods = ['POST'])
def log_in():
    user_name = request.form['username']
    password = request.form['password']
    login_user = db.userinfo.find_one({'username' : user_name , 'password' : password})
    if(login_user == None):
        print("실패")
        return jsonify({'message' : 'fail'})
    else:
        print("성공")
        access_token = create_access_token(identity=user_name)
        return jsonify(message = 'success', access_token = access_token)




@app.route('/register', methods = ['POST'])
def register():
    user_name = request.form['username']
    password = request.form['password']
    print(user_name)
    print(password)

    find_user = db.userinfo.find_one({'username' : user_name})
    if(find_user != None):
        return jsonify({'message' :'exist'})

    db.userinfo.insert_one({'username' : user_name, 'password' : password})
    print("회원가입성공")
    return jsonify({'message' : 'success'})

@app.route('/user')
@jwt_required()
def user_page():
    return render_template('index.html')

@app.route('/logout', methods=['POST'])
def log_out():
    response = jsonify({"message" : "success"})
    unset_jwt_cookies(response)
    return response

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)