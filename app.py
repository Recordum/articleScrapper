from flask import *
from pymongo import MongoClient
from bs4 import BeautifulSoup
from flask_jwt_extended import *
import requests

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "secret"
jwt = JWTManager(app)

client = MongoClient('localhost', 27017)
db = client.dbArticle


@app.route('/', methods = ['GET'])
def home():
    return render_template('home.html')

@app.route('/login', methods = ['POST'])
def log_in():
    user_name = request.form['username']
    password = request.form['password']
    login_user = db.userinfo.find_one({'username' : user_name , 'password' : password})
    if(login_user == None):
        print("실패")
        return jsonify({'message' : '로그인 정보를 다시 확인해 주세요'})
    else:
        print("성공")
        response = jsonify(message = "환영합니다")
        access_token = create_access_token(identity=user_name)
        response.set_cookie('access_token_cookie', access_token)

        return response


@app.route('/users', methods = ['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    find_user = db.userinfo.find_one({'username' : username})
    if(find_user != None):
        return jsonify({'message' :'존재하는 아이디 입니다'})

    db.userinfo.insert_one({'username' : username, 'password' : password, 'email' : email})
    print("회원가입성공")

    return jsonify({'message' : '회원가입 완료!'})

@app.route('/user-page')
@jwt_required(locations=['cookies'])
def user_page():
    return render_template("userpage.html")

@app.route('/user-page/article', methods = ['GET','POST'])
@jwt_required(locations=['cookies'])
def article():
    decode = decode_token(request.cookies['access_token_cookie'])
    username = decode['sub']
    if request.method == 'POST':
        url = request.form['url']
        comment = request.form['comment']
        try:
            score = request.form['score']
            score_validate = int(score)
        except:
            response = Response(status = 400)
            return response

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        og_title = soup.select_one('meta[property="og:title"]')
        og_description = soup.select_one('meta[property="og:description"]')
        og_img = soup.select_one('meta[property="og:image"]')

        title = og_title['content']
        description = og_description['content']
        img = og_img['content']
        print(img,description,title)
        db.scrap.insert_one({'username' : username, 'title' : title, 'description' : description, 'img' : img, 'comment' : comment, 'url': url ,'score' : score_validate})
        return jsonify({'username' : username, 'title' : title, 'description' : description, 'img' : img, 'comment' : comment, 'url': url,'score' : score_validate }),201
    else:
        articles = list(db.scrap.find({'username': username},{'_id' : False}))
        return jsonify({'articles' : articles}),200

@app.route('/user-page/article/<title>', methods = ['DELETE','POST'])
@jwt_required(locations=['cookies'])
def modify_article(title):
    decode = decode_token(request.cookies['access_token_cookie'])
    username = decode['sub']

    if request.method == "DELETE":
        db.scrap.delete_one({'username' : username, 'title' : title})
        return jsonify({'username' : username, 'title' : title, 'message' : 'delete_success'})
    else:
        comment = request.form['comment']
        try:
            score = request.form['score']
            score_validate = int(score)
        except:
            response = Response(status = 400)
            return response

        db.scrap.update_many({'username' : username, 'title' : title}, {'$set':{'comment' : comment, 'score' : score_validate}})
        return jsonify({'comment' : comment, 'score' : score_validate})
@app.route('/user-page/article/rank', methods = ['GET'])
@jwt_required(locations=['cookies'])
def movie_rank():
    decode = decode_token(request.cookies['access_token_cookie'])
    username = decode['sub']

    movies = list(db.scrap.find({'username' : username},{'_id' : False}))
    movies_sorted = sorted(movies, key = lambda x: x['score'], reverse = True)
    print(movies_sorted)
    return jsonify({'movies' : movies_sorted})

@app.route('/logout', methods=['POST'])
@jwt_required(locations=['cookies'])
def log_out():
    response = jsonify({"message" : "success"})
    response.set_cookie("access_token_cookie", '', expires=0)
    return response



if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)