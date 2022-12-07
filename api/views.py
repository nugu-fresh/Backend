from django.shortcuts import render
import json
import requests
from . import functions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from nugu_farm import nugu_settings
from django.db import connections
from django.http import JsonResponse


def health(request):
    return Response({'STATUS': '200 OK'}, status=200)


@api_view(['GET', 'POST'])
def price(request):
    if request.method == 'POST':
        pass
    
## Request Utterance parameter & Date-deciding Part ##   
    reqBody = json.loads(request.body, encoding='utf-8')
    actionName = reqBody.get('action').get('actionName')
    print(actionName)
    CROP_NAME = reqBody.get('action').get('parameters').get('u_crop').get('value')
    STD_DAY = reqBody.get('action').get('parameters').get('u_date').get('value')
    days, index, daycheck = functions.decide_Tense(STD_DAY) # Determine timedelta, KAMIS parsing index, tense check v.
    now_date, past_date, future_date = functions.decide_Date(days,daycheck) # Determine Exact date.

    if actionName == 'answerPrice':
        parameters = {
            'daycheck' : daycheck,
        }
## KAMIS API part ##
    global future_price
    global CROP_DICT
    global unit
    global now_price
    global past_price
    global dif
    future_price = 0

    if actionName == 'presentDate' or actionName =='pastDate' or actionName == 'futureDate':
        CROP_DICT = nugu_settings.CROP_DICTIONARY
        itemcode = CROP_DICT[f'{CROP_NAME}'][0]
        category_code = (int(itemcode) / 100) * 100
        kindcode = CROP_DICT[f'{CROP_NAME}'][1]
        kamis_key = nugu_settings.KAMIS_KEY
        kamis_id = nugu_settings.KAMIS_ID
        KAMIS_URL = f'http://www.kamis.or.kr/service/price/xml.do?action=periodProductList&p_productclscode=01&p_startday={past_date}&p_endday={now_date}&p_itemcategorycode={category_code}&p_itemcode={itemcode}&p_kindcode={kindcode}&p_productrankcode=04&p_countrycode=1101&p_convert_kg_yn=N&p_cert_key={kamis_key}&p_cert_id={kamis_id}&p_returntype=json'
        kamis_res = requests.get(KAMIS_URL)
        kamis_json = kamis_res.json()
        past_price = int(kamis_json['data']['item'][0]['price'].replace(',', ''))  # 과거
        now_price = int(kamis_json['data']['item'][index]['price'].replace(',', ''))  # 현재 (일주일전에서 현재가격으로 오려면 [5](주말제외)
        past_price = functions.scalePrice(CROP_NAME,past_price)
        now_price = functions.scalePrice(CROP_NAME,now_price)
        unit = CROP_DICT[f'{CROP_NAME}'][2]
    ## Parameters to JSON Response body  ##
        if daycheck == 0:
            parameters = {
                'now_price': now_price,
                'past_price': None,
                'change': None,
                'change_state': None,
                'daycheck': daycheck,
                'unit': unit,
            }
        elif daycheck == 1:
            dif = (now_price) - (past_price)
            if (dif > 0):
                parameters = {
                    'now_price': now_price,
                    'past_price': past_price,
                    'change': abs(dif),
                    'change_state': '원 만큼 오른',
                    'daycheck': daycheck,
                    'unit': unit,   
                }
            elif (dif < 0):
                parameters = {
                    'now_price': now_price,
                    'past_price': past_price,
                    'change': abs(dif),
                    'change_state': '원 만큼 내린',
                    'daycheck': daycheck,
                    'unit': unit,   
                }
            else:  
                parameters = {
                    'now_price': now_price,
                    'past_price': past_price,
                    'change': None,
                    'change_state': '변동없이',
                    'daycheck': daycheck,
                    'unit': unit,   
                }
        else:
            cursor = connections['default'].cursor()
            strSql = "select price from PriceOutput natural join FreshProfile where date='{}' and name='{}';".format(
                future_date, CROP_NAME)
            result = cursor.execute(strSql)
            rows = cursor.fetchall()
            future_price = int(rows[0][0])
            future_price = functions.scalePrice(CROP_NAME,future_price)
            dif = (now_price) - (future_price)
            if (dif > 0):
                parameters = {
                    'now_price': now_price,
                    'change': abs(dif),
                    'change_state': '원 비싼',
                    'daycheck': daycheck,
                    'future_price': future_price,
                    'unit': unit,   
                }
            elif (dif < 0):
                parameters = {
                    'now_price': now_price,
                    'change': abs(dif),
                    'change_state': '원 싼',
                    'daycheck': daycheck,
                    'future_price': future_price,
                    'unit': unit,   
                }
            else:  
                parameters = {
                    'now_price': now_price,
                    'change': None,
                    'change_state': '변동없이',
                    'daycheck': daycheck,
                    'future_price': future_price,
                    'unit': unit,   
                }
        
 ## Early Morning Delivery Part ##

    global kurly_price
    global ssg_price
    global coupang_price
    global cheapest
    global emd_name
    global url_text
    if actionName == 'askTwilioYesEMD':
        kurly_url = CROP_DICT[f'{CROP_NAME}'][3]
        ssg_url = CROP_DICT[f'{CROP_NAME}'][4]
        coupang_url = CROP_DICT[f'{CROP_NAME}'][5]

        kurly_price = functions.kurly_func(kurly_url,CROP_NAME)
        ssg_price = functions.ssg_func(ssg_url,CROP_NAME)
        coupang_price = functions.coupang_func(coupang_url,CROP_NAME)
        cheapest = min(min(coupang_price, kurly_price), ssg_price)
        if (cheapest == coupang_price):
            emd_name = '쿠팡'
            url_text = coupang_url
        elif (cheapest == kurly_price):
            emd_name = '컬리'
            url_text = kurly_url
        else:
            emd_name = 'SSG'
            url_text = ssg_url
        parameters = {}
        parameters['EMD_price'] = cheapest
        parameters['EMD_name'] = emd_name

## TWILIO Messaging Part ##
    
    if actionName == 'Y_YesTwilio' or actionName == 'N_Yes_Twilio':
        if daycheck == 0:
            body = f'*NUGU-FRESH*\n{CROP_NAME} {unit}의 현재가: {now_price}원\n{emd_name} 가격: {cheapest}원\nURL: {url_text}'
        elif daycheck == 1:
            body = f'*NUGU-FRESH*\n{CROP_NAME} {unit}의 현재가: {now_price}원\n{STD_DAY} 가격 : {past_price}원\n가격 변동: {dif}\n{emd_name} 가격: {cheapest}원\nURL: {url_text}'
        elif daycheck == 2:
            body = f'*NUGU-FRESH*\n{CROP_NAME} {unit}의 현재가: {now_price}원\n{STD_DAY} 가격 : {future_price}원\n가격 변동: {dif}\n{emd_name} 가격: {cheapest}원\nURL: {url_text}'
        else:
            body = 'Error'
        functions.send_Message(body)
        parameters={}

    response = {}
    response['version'] = reqBody.get('version')
    response['resultCode'] = 'OK'
    response['output'] = parameters

    return Response(response)