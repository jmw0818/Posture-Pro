from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'posture'

urlpatterns = [
    path('', views.login, name='login'),
    path('login', views.login),
    path('register', views.register, name='register'),
    path('check_username/', views.check_username, name='check_username'),

    path('main', views.main, name='main'),
    path('lunge', views.lunge, name='lunge'),
    path('flank', views.flank, name='flank'),
    path('squat', views.squat, name='squat'),
    path('pullup', views.pullup, name='pullup'),

    path('lunge_video', views.lunge_video, name='lunge_video'),
    path('pullup_video', views.pullup_video, name='pullup_video'),
    path('flank_video', views.flank_video, name='flank_video'),
    path('squat_video', views.squat_video, name='squat_video'),

    path('events', views.events, name='events'),
    path('result', views.result, name='result'),
    path('video_list', views.video_list, name='video_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
