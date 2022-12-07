from django.urls import path, include, re_path
from django.conf import settings
from . import views
urlpatterns = [
    path('health', views.health, name='health'),
    path('answerPrice', views.price, name='answerPrice'),
    path('presentDate', views.price, name='presentDate'),
    path('pastDate', views.price, name='pastDate'),
    path('futureDate',views.price, name='futureDate'),
    # path('noDate',views.wrong, name='noDate'),
    path('present_rewind', views.price, name='presentRewind'),
    path('past_rewind', views.price, name='pastRewind'),
    path('future_rewind',views.price, name='futureRewind'),
    path('askTwilioYesEMD', views.price, name='askTwilioYesEMD'),
    path('Y_YesTwilio', views.price, name='Y_YesTwilio'),
    path('N_Yes_Twilio', views.price, name='N_Yes_Twilio'),
]
