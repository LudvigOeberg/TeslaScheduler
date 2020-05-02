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
from datetime import datetime
from datetime import date


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#Class that holds the price of each hour
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

#Class that holds the average price of that day
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


tl = Timeloop()

#Function that loads credentials from file, sends a oauth request to Tesla API. Receive access token and save as a global varialble. Send a Vehicle list request and save ID as global variable
def login():
    params = {"grant_type" : "password",
    "client_secret" : "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3",
    "client_id" : "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"}
    file = open("teslapassword.txt","r")
    params.update({"password" : file.read()})
    file.close()
    file = open("teslaemail.txt","r")
    params.update({"email" : file.read()})
    file.close()

    #Sends login/oath request to Tesla
    response = requests.post("https://owner-api.teslamotors.com/oauth/token", data = params)
    data = response.json()
    access_token = data['access_token']
    global headers ##Kolla upp bättre lösning sen
    headers  = {"Authorization": "Bearer " + access_token}

    #Sends a request for vechicle list
    response1 = requests.get("https://owner-api.teslamotors.com/api/1/vehicles", headers = headers)
    data = response1.json()['response'][0]
    print(response1)
    global id #Kolla upp bättre lösning sen
    id =  data['id']
    print("Getting login information")

login()

@tl.job(interval=timedelta(hours = 1))
#Function that scrapes the hourly and average daily prices from elen.nu and adds them to database
def getPrices():
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
            if(len(alreadyExists) == 0):
                hourPrice = HourPrice(year = year, month = month, day = day, hour = hour, price = priceFloat)
                db.session.add(hourPrice)
                db.session.commit()
                print("Getting hourly prices")
    averagetable = r.html.find(".elspot-area-price")[2].text
    priceAverageString = (averagetable.split(" ")[0])
    priceAverageFloat1 = float(priceAverageString.split(",")[0])
    priceAverageFloat2 = float(priceAverageString.split(",")[1])/100
    priceAverage = priceAverageFloat1 + priceAverageFloat2

    alreadyExists2 = AveragePrice.query.filter_by(year=year,month=month, day=day).all()
    if(len(alreadyExists2) == 0):
        averagePrice = AveragePrice(year = year, month = month, day = day,priceAverage = priceAverage)
        db.session.add(averagePrice)
        db.session.commit()
        print("Getting daily averages")


#Every 10 hours calls login function to update API keys
@tl.job(interval=timedelta(hours = 10))
def callLogin():
    login()

#Function that gets charge information and activates/deactivates charging based on price information
@tl.job(interval=timedelta(minutes = 10))
def getTeslaData():
    #Gets charging informaton such as batter level and if currently charging
    response2 = requests.get("https://owner-api.teslamotors.com/api/1/vehicles/" + str(id) + "/data_request/charge_state", headers = headers)
    #If the car is asleep then wake it up
    if(response2.status_code == 408):
        response5 = requests.post("https://owner-api.teslamotors.com/api/1/vehicles/" + str(id) + "wake_up", headers = headers)
        print(response5.json())
        print("Waking car")
        getTeslaData()
    else:    
        data = response2.json()['response']
        currentCharge = data['battery_level']
        currentlyCharging = data['charge_enable_request']

        now = datetime.now()
        hour = now.strftime("%H")
        today = date.today()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        currentPrice = HourPrice.query.filter_by(year = year, month = month, day = day, hour = hour).all()
        averageCurrentPrice = AveragePrice.query.filter_by(year = year, month = month, day = day).all()
        #If the battery level is below 95% then decide if the car should charge or not
        if (currentCharge <= 95 ):
            #If there is no hourly price then load prices
            if(len(currentPrice) == 0):
                getPrices()
            else:
                #If the current hourly price is lower than the daily average price than charge, otherwise stop charging
                if(currentPrice[0].price <= averageCurrentPrice[0].priceAverage):
                    if(currentlyCharging == False):
                        response3 = requests.post("https://owner-api.teslamotors.com/api/1/vehicles/" + str(id) + "/command/charge_start", headers = headers)
                        data = response3.json()
                        print(data)
                        print(day+ " " + hour + " " + "Starting to charge")
                        
                    else:
                        print(day+ " " + hour + " " + "Already charging")
                else :
                    if(currentlyCharging == True):
                        response3 = requests.post("https://owner-api.teslamotors.com/api/1/vehicles/" + str(id) + "/command/charge_stop", headers = headers)
                        data = response3.json()
                        print(data)
                        print(day+ " " + hour + " " + "Stopping charging")
                    else:
                        print(day+ " " + hour + " " + "Charging already off")

if __name__ == "__main__": 
    tl.start(block=True)
