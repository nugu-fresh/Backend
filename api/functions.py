import requests
import json
from bs4 import BeautifulSoup
import datetime
from nugu_farm import nugu_settings
from twilio.rest import Client


## Deciding Tense of Utterances ##
def decide_Tense(STD_DAY):
    global days
    global index
    global daycheck

    if STD_DAY == '오늘' or STD_DAY == '현재':
        days = 0
        index = 0
        daycheck = 0
    elif STD_DAY == '어제':
        days = -1
        index = 1
        daycheck = 1
    elif STD_DAY == '일주일전' or STD_DAY == '지난 주' or STD_DAY == '지난주':
        days = -7
        index = 5
        daycheck = 1
    elif STD_DAY == '한달전' or STD_DAY == '지난달':
        days = -28
        index = 25
        daycheck = 1
    elif STD_DAY == '내일':
        days = 1
        index = 0
        daycheck = 2
    elif STD_DAY == '이일후':
        days = 2
        index = 0
        daycheck = 2
    elif STD_DAY == '삼일후':
        days = 3
        index = 0
        daycheck = 2
    elif STD_DAY == '사일후':
        days = 4
        index = 0
        daycheck = 2
    elif STD_DAY == '오일후':
        days = 5
        index = 0
        daycheck = 2
    elif STD_DAY == '육일후':
        days = 6
        index = 0
        daycheck = 2
    elif STD_DAY == '다음주':
        days = 7
        index = 0
        daycheck = 2
    return (days,index,daycheck)

## Deciding Exact Date ##
def decide_Date(days,daycheck):
    td = datetime.timedelta(days=days)
    if daycheck == 0:
        now_date = datetime.date.today() + datetime.timedelta(days=-1)  # 최신 업데이트날짜
        past_date = now_date + td  # 유동 timedelta 추가
        future_date = None
    elif daycheck == 1:
        now_date = datetime.date.today() + datetime.timedelta(days=-1)  # 최신 업데이트날짜
        past_date = now_date + td  # 유동 timedelta 추가
        future_date = None
    elif daycheck == 2:
        now_date = datetime.date.today() + datetime.timedelta(days=-1)
        past_date = datetime.date.today() + datetime.timedelta(days=-1)
        future_date = now_date+ datetime.timedelta(days=1) + td
    return (now_date,past_date,future_date)

## Scaling KAMIS price ##
def scalePrice(crop_name, price):
    if crop_name == '양파':
        return int(price*3)
    elif crop_name == '쌀':
        return int(price/2)
    elif crop_name == '감자':
        return int(price*10)
    else:
        return price

 ## Crawlers ##

def kurly_func(kurly_url,crop_name):
    headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    response = requests.get(kurly_url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    pre_json = soup.select_one('#__NEXT_DATA__').text
    jsonObject = json.loads(pre_json)
    kurlySpecific = jsonObject['props']['pageProps']['product']['dealProducts'][0]

    if kurlySpecific['discountedPrice']== None:
        kurlyPrice=int(kurlySpecific['basePrice'])
    else:
        kurlyPrice=int(kurlySpecific['discountedPrice'])
    return kurlyPrice


def coupang_func(coupang_url,crop_name):
    headers = {
        "authority": "www.coupang.com",
        "method": "GET",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.104 Whale/3.13.131.36 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
    }

    response = requests.get(coupang_url, headers=headers)
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    price = soup.find_all('span', attrs={'class': 'total-price'})
    price = price[0].text
    coupangPrice = price.replace(',', '').replace('원','')
    coupangPrice = int(coupangPrice)
    return coupangPrice


def ssg_func(ssg_url,crop_name): 
    headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    response = requests.get(ssg_url, headers=headers)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    ssg_text = soup.find('em',class_='ssg_price').text
    ssgPrice = int(ssg_text.replace(',',''))
    if crop_name == '양파':
        ssgPrice *= (3.0/1.8)
    elif crop_name == '감자':
        ssgPrice /= 2

    return int(ssgPrice)

## Twilio Messaging part ##
def send_Message(body):
    account_sid = nugu_settings.TWILIO_SID
    auth_token = nugu_settings.TWILIO_TOKEN

    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        to='+821036962631',  # verified 
        from_='+18643839587',  # twilio trial
        body=body
    )

# def weekday(whenever):
#     days = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
#     num = whenever.weekday()
#     if days[num] =='토요일' or days[num] == '일요일':
#         return 1
#     return 0
    