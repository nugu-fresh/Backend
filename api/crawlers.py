import requests
import json
from bs4 import BeautifulSoup

##### 컬리 성공 샛별배송 브랜드로만 가능#######
def kurly_func(kurly_url):
    kurly_url=f'https://www.kurly.com/goods/5000070' 
    headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    response = requests.get(kurly_url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    pre_json = soup.select_one('#__NEXT_DATA__').text
    jsonObject = json.loads(pre_json)
    kurlySpecific = jsonObject['props']['pageProps']['product']['dealProducts'][0]

    #----------------이름에서 g, kg 인지 구분해서 100g 단위 가격으로 맞추기 위한 배수(volume_weight) 찾기----------------#  
    volume_text = kurlySpecific['name']
    print(volume_text)
    if(volume_text[-1]=='g' and volume_text[-2]=='k'): # 킬로그램 단위일 때
        i=2
        while(volume_text[-i]!=' '): # 공백을 만나는 것으로 숫자부분 index를 체크하고 break
            i=i+1
        i=i-1 
        volume_weight = (int(volume_text[-i:-2]))*10 #Nkg은 N000g이니 100g의 10배 볼륨
    elif(volume_text[-1]=='g'): # 그램 단위일 때
        i=1
        while(volume_text[-i]!=" "):
            i=i+1
        i=i-1 
        volume_weight = (int(volume_text[-i:-1]))/100 # N백g이니 100을 나눠주면 N 추출
    #---------------------volume_weight으로 kurlyPrice를 나눠주면 100g 당 가격 추출 -----------------#
    if(kurlySpecific['discountedPrice']== None):
        kurlyPrice=kurlySpecific['basePrice']
    else:
        kurlyPrice=kurlySpecific['discountedPrice']
    price_100g=float(kurlyPrice)/volume_weight
    return price_100g

##### SSG 수정완료 SSG.fresh 브랜드로만 가능 ####
def ssg_func(ssg_url):     #ssg_url
    ssg_url = 'https://www.ssg.com/item/itemView.ssg?itemId=2097000834177&siteNo=7009&salestrNo=2449&tlidSrchWd=SSG.fresh&srchPgNo=1&src_area=ssglist'
    headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    response = requests.get(ssg_url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    ssg_text=soup.select_one('#content > div.cdtl_cm_detail.ty_ssg.react-area > div.cdtl_row_top > div.cdtl_col_rgt > div.cdtl_info_wrap > div.cdtl_optprice_wrap > p').text
    for i in range(len(ssg_text)):
        if(ssg_text[i]=='g'): # 단위 추출
            volume=int(ssg_text[23:i])
        elif(ssg_text[i]==' '):
            empty=i
        elif(ssg_text[i]=='원'): #가격 추출
            price = ssg_text[empty+1:i]
            price = price.replace(",","")
            price = price.replace(':\n\t','')
            price=int(price)
            break
        else:
            continue
    if volume == 100: #단위 100g 맞는지 확인 
        ssgPrice = price
    elif volume == 10: #10g이면 100g으로 변환
        ssgPrice= price*10
    else:
        ssgPrice=f'{volume}g 당 {price}' #100g도 10g도 아니면 있는 그대로 문자열로
    return ssgPrice
#TODO 컬리랑 SSG는 각각 샛별배송과 SSG.fresh 브랜드에 맞춰서 100g 당 가격 추출 완료. url만 작물에 맞게 바꿔주면 됨
#TODO 쿠팡은 왜인지 response를 못받는건지 requests가 안가는건지 시작도 못함

def coupang_func():
    coupangPrice=0
    return coupangPrice