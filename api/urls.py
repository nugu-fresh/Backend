from django.urls import path, include, re_path
from django.conf import settings
from . import views
urlpatterns = [
    # path('main/',views.main, name='main'),
    path('health',views.health, name='health'),
    path('price', views.price, name='price'),
    path('presentDate', views.price, name='presentDate'),
    path('pastDate', views.price, name='pastDate'),
    path('futureDate',views.price, name='futureDate'),
    path('present_yesEMD', views.price, name='presentYEMD'),
    path('past_yesEMD', views.price, name='pastYEMD'),
    path('future_yesEMD', views.price, name='futureYEMD'),
    path('present_noEMD', views.price, name='presentYEMD'),
    path('past_noEMD', views.price, name='pastYEMD'),
    path('future_noEMD', views.price, name='futureYEMD'),
    path('askTwilioYesEMD', views.price, name='yesemd'),
    path('ask.Twilio.noEMD', views.price, name='noemd'),
    path('Yes_Twilio', views.price, name='yestwilio'),
    path('No_Twilio', views.price, name='notwilio'),
    path('yesyes', views.price, name='yesyes'),
    path('nono', views.price, name='nono'),


]
