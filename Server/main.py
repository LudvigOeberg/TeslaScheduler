import json
from flask import Flask
from flask import jsonify
from flask import abort
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__,static_folder='../Client', static_url_path='/' )
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class HourPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable = False)
    month = db.Column(db.Integer, nullable = False)
    day = db.Column(db.Integer, nullable = False)
    hour = db.Column(db.Integer, nullable = False)
    price = db.Column(db.Float, nullable = False)

    def __repr__(self):
        return '<Hourprice {}: {} {} {} {} {}>'.format(self.id, self.year, self.month,self.day, self.hour, self.price)

    def serialize(self):
        return dict(id = self.id, year = self.year, month = self.month, day = self.day, hour =  self.hour, price = self.price)


class AveragePrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable = False)
    month = db.Column(db.Integer, nullable = False)
    day = db.Column(db.Integer, nullable = False)
    priceAverage = db.Column(db.Float, nullable = False)

    def __repr__(self):
        return '<Hourprice {}: {} {} {} {}>'.format(self.id, self.year, self.month,self.day, self.priceAverage)

    def serialize(self):
        return dict(id = self.id, year = self.year, month = self.month, day = self.day,priceAverage = self.priceAverage)


@app.route('/')
def hello():
    return app.send_static_file("home.html")



if __name__ == "__main__": 
     app.run(host='localhost',port='5001', debug=True)

