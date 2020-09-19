from datetime import datetime

from flask import Flask, redirect, abort
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/projdoc'
mongo = PyMongo(app)

# url = mongo.db.users.find_one({'uid': 187471109})['seminars']['4']
# mongo.db.users.update_one({'uid': 187471109}, {'$set': {'seminars.4.url': 1}})


@app.route('/')
def index():
    return redirect('https://online.hse.ru/course/view.php?id=1845')


@app.route('/<key>')
def url(key):
    url = mongo.db.urls.find_one({'key': key})
    if not url or datetime.now() >= url['exp_dt']:
        return abort(404)

    mongo.db.users.update_one({'uid': url['uid']}, {
        '$push': {
            f'seminars.{url["sem_num"]}.url_clicks': datetime.now()
        }
    })

    return redirect(url['url'])


if __name__ == '__main__':
    app.run('0.0.0.0', port=80)
