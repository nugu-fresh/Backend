from django.shortcuts import render
import json
import datetime
import requests
from . import crawlers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twilio.rest import Client
from nugu_farm import nugu_settings
from django.db import connections
from django.http import JsonResponse
# Create your views here.
def health(request):
    return Response({'STATUS': '200 OK'}, status=200)

@api_view(['GET','POST'])
def price(request):
    if request.method == 'POST':
        pass
    reqBody = json.loads(request.body, encoding='utf-8')
    CROP_NAME = reqBody.get('action').get('parameters').get('u_crop').get('value')
    STD_DAY = reqBody.get('action').get('parameters').get('u_date').get('value')
    # 토일 가격 비는 문제 해결해야함
    if STD_DAY=='오늘' or STD_DAY=='현재':
        days = 0
        index = 0
        daycheck = 0
    elif STD_DAY=='일주일전' or STD_DAY== '지난주':
        days = -7
        index = 5
        daycheck = 1
    elif STD_DAY=='한달전' or STD_DAY == '지난달':
        days = -35
        index = 25
        daycheck = 1
    elif STD_DAY=='내일':
        days = 1
        daycheck = 2
    elif STD_DAY=='이일후':
        days = 2
        daycheck = 2
    elif STD_DAY=='삼일후':
        days = 3
        daycheck = 2
    elif STD_DAY=='사일후':
        days = 4
        daycheck = 2
    elif STD_DAY=='오일후':
        days = 5
        daycheck = 2
    elif STD_DAY=='육일후':
        days = 6
        daycheck = 2
    elif STD_DAY=='다음주':
        days = 7
        daycheck = 2

    td = datetime.timedelta(days=days)

    if daycheck == 0:
        now_date = datetime.date.today() + datetime.timedelta(days=-1) #최신 업데이트날짜
        past_date= now_date+ td # 유동 timedelta 추가
    elif daycheck == 1:
        now_date = datetime.date.today() + datetime.timedelta(days=-1) #최신 업데이트날짜
        past_date= now_date+ td # 유동 timedelta 추가
    elif daycheck == 2:
        past_date=None
        now_date = datetime.date.today()
        future_date = now_date + td 
    global future_price # 밑에서 전역변수 설정 예정
    future_price = 0
    if daycheck == 0 or daycheck == 1:
        CROP_DICT = nugu_settings.CROP_DICTIONARY
        itemcode = CROP_DICT[f'{CROP_NAME}'][0]
        category_code = (int(itemcode)/100)*100
        kindcode = CROP_DICT[f'{CROP_NAME}'][1]
        kamis_key = nugu_settings.KAMIS_KEY
        kamis_id = nugu_settings.KAMIS_ID
        KAMIS_URL = f'http://www.kamis.or.kr/service/price/xml.do?action=periodProductList&p_productclscode=01&p_startday={past_date}&p_endday={now_date}&p_itemcategorycode={category_code}&p_itemcode={itemcode}&p_kindcode={kindcode}&p_productrankcode=04&p_countrycode=1101&p_convert_kg_yn=Y&p_cert_key={kamis_key}&p_cert_id={kamis_id}&p_returntype=json'
        kamis_res = requests.get(KAMIS_URL)
        kamis_json = kamis_res.json()
        past_price = int(kamis_json['data']['item'][0]['price'].replace(',','')) #과거
        
        now_price = int(kamis_json['data']['item'][index]['price'].replace(',','')) #현재 (일주일전에서 현재가격으로 오려면 [5](주말빼서)
        

            ####### daycheck: 현재=0 과거=1 미래=2 오류=-1
            ## change calculation part ##
    if daycheck == 0:
        parameters = {
            'now_price' : now_price,
            'past_price' : None,
            'change' : None,
            'change_state' : None,
            'daycheck' : daycheck,
        }
    elif daycheck == 1:
        dif = (now_price) - (past_price)
        if(dif>0):
            parameters = {
            'now_price' : now_price,
            'past_price' : past_price,
            'change': abs(dif),
            'change_state' : '원 만큼 오른',
            'daycheck' : daycheck,   
        }
        elif(dif<0):
            parameters = {
            'now_price' : now_price,
            'past_price' : past_price,
            'change': abs(dif),
            'change_state' : '원 만큼 내린', 
            'daycheck' : daycheck,    
        }
        else: #if(dif==0) #TODO NUGU 액션에서 change가 None일 때 발화 패턴 다르게 해줘야함
            parameters = {
                'now_price' : now_price,
                'past_price' : past_price,
                'change': None,
                'change_state' : '동일하게', 
                'daycheck' : daycheck,  
            }
    else:

    ##################################################################################################
    ## EMD Part ##

    #TODO 오늘 어제로 뽑았을때 단위가 뒤죽박죽으로 반환돼서 이거 생각해야함 (포기 단위도 있음)
    #TODO 크롤러로 쿠팡프레시,컬리,쓱 가격 가져와서
    # kurly_url = CROP_DICT[f'{CROP_NAME}'][2]
    # ssg_url = CROP_DICT[f'{CROP_NAME}'][3]
    # coupang_url = CROP_DICT[f'{CROP_NAME}'][4]
    # kurly_price=crawlers.kurly_func(kurly_url)
    # ssg_price=crawlers.ssg_func(ssg_url)
    # coupang_price=crawlers.coupang_func(coupang_url)
    kurly_price=0
    ssg_price=0
    coupang_price=0
    ###################################################################################################
    #셋 중 최저가 골라서
    cheapest=min(min(coupang_price, kurly_price),ssg_price)
    if(cheapest==coupang_price):
        emd_name='쿠팡'
    elif(cheapest==kurly_price):
        emd_name='컬리'
    else:
        emd_name='SSG'

    # TWILIO action일 때
    actionName=reqBody.get('action').get('actionName')
    print(actionName)
    if actionName == 'Yes_Twilio' or actionName == 'yesyes':
        account_sid = nugu_settings.TWILIO_SID
        auth_token = nugu_settings.TWILIO_TOKEN

        client = Client(account_sid, auth_token)
        if daycheck==1:
            change=now_price-past_price
        if daycheck==0:
            print('daycheck까지 왔음')
            body=f'*NUGU-FRESH*\n{CROP_NAME}의 현재가: {now_price}원\n{emd_name} 가격: {cheapest}원\n'
        elif daycheck==1:
            body=f'*NUGU-FRESH*\n{CROP_NAME}의 현재가: {now_price}원\n{STD_DAY} 가격 : {past_price}원\n가격 변동: {change}\n{emd_name} 가격: {cheapest}원\n'
        elif daycheck==2:
            body=f'*NUGU-FRESH*\n{CROP_NAME}의 {STD_DAY} 가격 : {future_price}원\n{emd_name} 가격: {cheapest}원\n'
        else:
            body='잘못된 날짜입력'
        message = client.messages.create(
            to='+821036962631', # verified 되어있는 김봉균 번호
            from_='+18643839587',  # twilio 유료버전 구매하면 그 번호로 바꿔줘야함 
            body=body
        )

    parameters['EMD_price'] = cheapest
    parameters['EMD_name'] = emd_name
    
    ## 헤더 붙여서 Response ##
    response = {}
    response['version']=reqBody.get('version')
    response['resultCode']='OK'
    response['output']= parameters

    return Response(response)
