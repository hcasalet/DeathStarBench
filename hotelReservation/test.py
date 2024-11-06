import math
import requests
import random
import time


def hotels():

    url = "http://localhost:5000/hotels"
    in_date = 17
    out_date = 18

    in_date_str = str(in_date)
    if in_date <= 9:
        in_date_str = "2015-04-0" + in_date_str 
    else:
        in_date_str = "2015-04-" + in_date_str
    

    out_date_str = str(out_date)
    if out_date <= 9:
        out_date_str = "2015-04-0" + out_date_str 
    else:
        out_date_str = "2015-04-" + out_date_str
    

    lat = 38.0235 
    lon = -122.095 

    payload = {"inDate": in_date_str , "outDate": out_date_str, "lat": lat, "lon": lon}

    t_before = time.time()
    r = requests.get(url, params=payload)
    t_after = time.time()
    t = t_after - t_before
    print(r.text)
    print("hotel=",t)

def reviews():
    url = "http://localhost:5000/review"
    payload = {"hotelId":"2", "username": "Cornell_0", "password": "0000000000"}
    t_before = time.time()
    r = requests.get(url, params=payload)
    t_after = time.time()
    t = t_after - t_before
    print(r.text)
    print("review=",t)

hotels()