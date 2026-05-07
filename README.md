# PosturePro

운동 영상을 업로드하면 AI가 관절 좌표를 분석하여 자세 점수와 피드백을 제공하는 웹 애플리케이션입니다.

> **본 저장소는 졸업 프로젝트 원본을 포트폴리오 목적으로 리팩토링한 버전입니다.**
> 졸업 제출 원본은 [python-django](https://github.com/jmw0818/python-django) 저장소에 보존되어 있습니다.

## 주요 개선 사항 (원본 대비)

- 중첩된 폴더 구조(`v1/v1/v1/`) → 단일 루트 구조로 재편
- 1300줄 단일 `views.py` → `posture/pose/` 모듈로 분리
- 설정 패키지 `v1/` → `config/`, 앱 패키지 `v3/` → `posture/`로 명확한 이름으로 변경
- 비로그인 접근 시 500 에러 수정 (로그인 페이지 리다이렉트)
- 결과 화면 새로고침 시 기록 중복 저장 버그 수정
- 비밀번호 평문 저장 → 해싱 처리

## 구현 기능

| 기능 | 상태 |
|------|------|
| 회원가입 / 로그인 | 완료 |
| 런지 (Lunge) 자세 분석 | 완료 |
| 풀업 (Pull Up) 자세 분석 | 완료 |
| 스쿼트 (Squat) 자세 분석 | 완료 |
| 플랭크 (Flank) 자세 분석 | 완료 |
| 운동 기록 저장 및 차트 시각화 | 완료 |
| 자세 피드백 텍스트 | 런지만 구현 |

## 기술 스택

- Python 3.x / Django 5.0
- OpenPose (Caffe)
- OpenCV, Pandas
- Bootstrap 5, ApexCharts

## 폴더 구조

```
졸작/
├── manage.py
├── config/                 Django 프로젝트 설정 (settings, urls, wsgi, asgi)
├── posture/                메인 앱
│   ├── views.py
│   ├── models.py
│   ├── urls.py
│   └── pose/               자세 분석 모듈
│       ├── utils.py
│       ├── lunge.py
│       ├── pullup.py
│       ├── squat.py
│       └── flank.py
├── templates/v2/           HTML 템플릿
├── static/                 정적 파일
└── *.prototxt              OpenPose 모델 설정 파일
```

---

## 설치 및 실행 방법

### 1. 레포지토리 클론

```bash
git clone https://github.com/jmw0818/Posture-Pro.git
cd Posture-Pro
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install django pandas opencv-python django-sass-processor
```

### 3. OpenPose 모델 파일 다운로드 (필수)

모델 파일은 용량 문제로 저장소에 포함되지 않습니다. 아래 링크에서 직접 다운받아 프로젝트 루트(`manage.py`와 같은 위치)에 넣어주세요.

| 파일명 | 용도 | 다운로드 |
|--------|------|----------|
| `pose_iter_584000.caffemodel` | Lunge / Flank 분석 (Body25) | [Google Drive](https://drive.google.com/file/d/1nB5c19yAHBFMoqU0S2xQUDk9xIECMGOW/view?usp=sharing) |
| `pose_deploy.prototxt` | Body25 모델 설정 | 이 저장소에 포함됨 |
| `pose_iter_160000.caffemodel` | Squat / Pull Up 분석 (MPII) | [Google Drive](https://drive.google.com/file/d/1c9SXQZ3KGMgKmyq-sNsn8x7TuXHe-9xT/view?usp=sharing) |
| `pose_deploy_linevec_faster_4_stages.prototxt` | MPII 모델 설정 | 이 저장소에 포함됨 |

> 공식 출처: [CMU OpenPose GitHub](https://github.com/CMU-Perceptual-Computing-Lab/openpose)

### 4. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 5. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000/` 접속
