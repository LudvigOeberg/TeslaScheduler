import json
from flask import Flask
from flask import jsonify
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from requests_html import HTML, HTMLSession
import datetime
import time
import requests
from timeloop import Timeloop
from datetime import timedelta


app = Flask(__name__)
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


session = HTMLSession() 
r = session.get('https://elen.nu/timpriser-pa-el-for-elomrade-se3-stockholm')
datetable = r.html.find('tr')
for tr in datetable:
    date = tr.find('td', first = True)
    if (date != None):
        date = date.text
        year = date.split('-')[0]
        month = date.split('-')[1]
        splitday = date.split('-')[2]
        day = splitday.split(' ')[0]
        time = date.split(" ")[1]
        hour = time.split(":")[0]
        priceList = tr.find('td')
        counter = 0
        for price in priceList:
            counter = counter +1 
            if (counter % 2 == 0):
                amount = price.text
                priceString = amount.split(" ")[0]
                priceFloat = float(priceString)
        alreadyExists = HourPrice.query.filter_by(year=year,month=month, day=day, hour=hour).all()
        if(alreadyExists == None):
            hourPrice = HourPrice(year = year, month = month, day = day, hour = hour, price = priceFloat)
            db.session.add(hourPrice)
            db.session.commit()
averagetable = r.html.find(".elspot-area-price")[2].text
priceAverageString = (averagetable.split(" ")[0])
priceAverageFloat1 = float(priceAverageString.split(",")[0])
priceAverageFloat2 = float(priceAverageString.split(",")[1])/100
priceAverage = priceAverageFloat1 + priceAverageFloat2

alreadyExists2 = AveragePrice.query.filter_by(year=year,month=month, day=day).all()
if(alreadyExists2 == None):
    averagePrice = AveragePrice(year = year, month = month, day = day,priceAverage = priceAverage)
    db.session.add(averagePrice)
    db.session.commit()


params = {
"email" : "tesla@ludvigoberg.me",
"password" : "8WboW9aV6Bnq%3",
"grant_type": "password",
"client_secret" : "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3",
"client_id" : "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"}
response = requests.post("https://owner-api.teslamotors.com/oauth/token", data = params)
data = response.json()
access_token = data['access_token']
headers = {"Authorization": "Bearer " + access_token}

response1 = requests.get("https://owner-api.teslamotors.com/api/1/vehicles", headers = headers)
data = response1.json()['response'][0]
id = data['id']


response2 = requests.get("https://owner-api.teslamotors.com/api/1/vehicles/" + str(id) + "/data_request/charge_state", headers = headers)
data = response2.json()['response']
currentCharge = data['battery_level']
currentlyCharging = data['charge_enable_request']
print(currentCharge)
print(currentlyCharging)

if ( currentCharge <= 95 ) :

    ##Insert logic here later


if __name__ == "__main__": 
     app.run(debug=True)