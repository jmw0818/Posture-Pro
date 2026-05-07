import os
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from .models import UserModel, UserRank, Video, RankHistory
from .pose.lunge import lunge_tool
from .pose.pullup import pullup_tool
from .pose.squat import squat_tool
from .pose.flank import flank_tool


def _require_login(request):
    if not request.session.get('username'):
        return redirect('posture:login')
    return None


def main(request):
    redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response
    username = request.session.get('username')
    rank_history = RankHistory.objects.filter(user=username)

    rank_values = [history.rank_value for history in rank_history]
    timestamps = [history.timestamp.strftime("%Y-%m-%d") for history in rank_history]
    postures = [history.posture for history in rank_history]
    labels = [f"{timestamp} \n {posture}" for timestamp, posture in zip(timestamps, postures)]

    chart_data = {
        'rank_values': rank_values,
        'labels': labels,
    }

    context = {
        'rank_history': rank_history,
        'username': username,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'main.html', context)


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        try:
            me = UserModel.objects.get(username=username)
            if check_password(password, me.password):
                request.session['username'] = me.username
                return redirect('posture:main')
            else:
                return render(request, 'login.html', {'error': '비밀번호가 틀렸습니다.'})
        except UserModel.DoesNotExist:
            return render(request, 'login.html', {'error': '계정이 존재하지 않습니다.'})
    return render(request, 'login.html')


def password(request):
    return render(request, 'password.html')


def register(request):
    if request.method == "POST":
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        password2 = request.POST.get('password2', None)
        if password != password2:
            return render(request, 'register.html')
        new_user = UserModel()
        new_user.username = username
        new_user.password = make_password(password)
        new_user.save()
        return render(request, 'login.html')
    return render(request, 'register.html')


def check_username(request):
    if request.method == "GET":
        username = request.GET.get('username', None)
        exists = UserModel.objects.filter(username=username).exists()
        return JsonResponse({'exists': exists})


def lunge(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'lunge.html')

def flank(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'flank.html')

def squat(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'squat.html')

def pullup(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'pullup.html')

def events(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'events.html')

def video_list(request):
    return redirect_response if (redirect_response := _require_login(request)) else render(request, 'video_list.html')


def import_csv_to_model(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path, encoding='euc-kr')
        count_correct = len(df[df['Posture'] == '올바른 자세'])
        count_incorrect = len(df[df['Posture'] == '올바르지 못한 자세'])
        rank_value = count_correct / (count_correct + count_incorrect) * 100
        UserRank.objects.create(rank=str(rank_value))
        return rank_value
    except Exception as e:
        print(f"Error in import_csv_to_model: {e}")
        return None


def result(request):
    redirect_response = _require_login(request)
    if redirect_response:
        return redirect_response

    username = request.session.get('username')
    style = request.session.get('style', 'default_style')

    user = UserModel.objects.get(username=username)
    context = {'user': user, 'username': username}

    csv_file_paths = {
        'lunge': "frame_point/lunge/lunge_co/all_points.csv",
        'pullup': "frame_point/pullup/pullco/all_points.csv",
        'squat': "frame_point/squat/squatco/all_points.csv",
        'flank': "frame_point/flank/flank_co/all_points.csv",
    }

    csv_text = ""
    rank_value = 0

    csv_file_path = csv_file_paths.get(style)
    if csv_file_path and os.path.exists(csv_file_path):
        try:
            rank_value = import_csv_to_model(csv_file_path)
            if not request.session.get('result_saved'):
                RankHistory.objects.create(user=user, rank_value=rank_value, posture=style)
                request.session['result_saved'] = True
            df = pd.read_csv(csv_file_path, encoding='euc-kr')

            if style == 'lunge':
                incorrect_postures = df[df['Posture'] == '올바르지 못한 자세']
                if not incorrect_postures.empty:
                    incorrect = incorrect_postures.iloc[0]
                    front = incorrect['front']
                    if front == 'right':
                        angle = incorrect['knee_angle_right']
                        csv_text = '오른쪽 무릎의 각도가 충분하지 않습니다. 허벅지와 종아리 근육을 사용해 조금 더 깊게 굽혀 안정된 자세를 유지해 주세요.' \
                            if angle - 80 > 0 else \
                            '전체적으로 오른쪽 무릎이 과도하게 굽혀졌습니다.\n 무릎 관절에 무리가 갈 수 있으니, 다리를 약간 덜 굽혀 체중을 고르게 분산해 주세요.'
                    elif front == 'left':
                        angle = incorrect['knee_angle_left']
                        csv_text = '왼쪽 무릎의 각도가 충분하지 않습니다. 무릎과 허벅지를 더 많이 사용하여 균형을 잡고, 적절한 깊이로 내려가 주세요.' \
                            if angle - 80 > 0 else \
                            '왼쪽 무릎이 과도하게 굽혀졌습니다. 관절 손상을 예방하기 위해 무릎을 약간 덜 굽히고 체중을 고르게 분산시켜주세요.'
                    else:
                        csv_text = "올바르지 않은 자세가 감지되었습니다. 선택하신 자세가 맞으십니까?"
                else:
                    csv_text = "훌륭합니다! 모든 프레임에서 올바른 자세가 감지되었습니다."
            else:
                csv_text = "분석이 완료되었습니다."

        except Exception as e:
            print(f"Error in result view: {e}")
            csv_text = "데이터 처리 중 오류가 발생했습니다."
    else:
        csv_text = "CSV 파일을 찾을 수 없습니다."

    videos = Video.objects.all()
    return render(request, 'result.html', {
        'videos': videos,
        'csv_text': csv_text,
        'rank_value': rank_value,
        'context': context,
    })


def _save_video(request, style_name):
    request.session['result_saved'] = False
    if request.method == "POST" and 'document' in request.FILES:
        document = request.FILES["document"]
        new_file_name = f"{style_name}_test"
        existing_file_path = os.path.join(settings.MEDIA_ROOT, new_file_name + ".mp4")
        if os.path.exists(existing_file_path):
            os.remove(existing_file_path)
        Video.objects.all().delete()
        file_extension = os.path.splitext(document.name)[1]
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(f"{new_file_name}{file_extension}", document)
        Video(title=f"{new_file_name}{file_extension}", document=filename).save()
    return Video.objects.latest('upload_date') if Video.objects.exists() else None


def lunge_video(request):
    latest_video = _save_video(request, 'lunge')
    lunge_tool(request)
    return render(request, "events.html", context={"video": latest_video})


def pullup_video(request):
    latest_video = _save_video(request, 'pullup')
    pullup_tool(request)
    return render(request, "events.html", context={"video": latest_video})


def squat_video(request):
    latest_video = _save_video(request, 'squat')
    squat_tool(request)
    return render(request, "events.html", context={"video": latest_video})


def flank_video(request):
    latest_video = _save_video(request, 'flank')
    flank_tool(request)
    return render(request, "events.html", context={"video": latest_video})
