from requests_html import HTML, HTMLSession
from main import db,AveragePrice, HourPrice
import datetime
import time
from timeloop import Timeloop
from datetime import timedelta


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
