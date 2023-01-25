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
        print(response)
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

@app.route('/userpage/<username>')
@jwt_required(locations=['cookies'])
def user_page(username):
    decode = decode_token(request.cookies['access_token_cookie'])
    token_username = decode['sub']
    if token_username != username:
        print('허용되지않음')
        response = Response(status=401)
        return response

    return render_template("userpage.html")


@app.route('/username/movie-rank')
@jwt_required(locations=['cookies'])
def movie_rank():
    return render_template('movierank.html')
@app.route('/logout', methods=['POST'])
@jwt_required(locations=['cookies'])
def log_out():
    response = jsonify({"message" : "success"})
    response.set_cookie("access_token_cookie", '', expires=0)
    return response

@app.route('/<username>/article', methods=['POST','GET','DELETE'])
def article(username, url):
    if request.method == "POST":
        comment = request.form.get['comment'];

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup.get(response, 'html.parser')

        og_title = soup.select_one('meta[property="og:title"]')
        og_description = soup.select_one('meta[property="og:description"]')
        og_img = soup.select_one('meta[property="og:image"]')

        title = og_title['content']
        description = og_description['content']
        img = og_img['content']

        db.article.insert_one({'username': username, 'title' : title, 'description' : description, 'img' : img, 'comment' : comment, 'url':url})
        return jsonify(message = 'add_article_success')

    elif request.methods == "GET":
        all_article = list(db.article.find({}, {'_id' : False}))
        return jsonify(all_article)

    else:
        url = request.form.get['url'];
        comment = request.form.get['comment'];

        db.article.delete_one({'url' : url, 'comment':comment, 'username' : username})
        return jsonify(message = 'delete_article_Success')


if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)