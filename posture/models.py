from django.db import models

from django.utils import timezone

class UserRank(models.Model):
    class Meta:
        db_table = "my-user_rank"
    
    rank = models.CharField(max_length=100, default='')
    timestamp = models.DateTimeField(default=timezone.now)  # 기록 시간 
    def __str__(self):
        return self.rank

class RankScore(models.Model):
    class Meta:
        db_table = "my-rank_scores"
    
    user_rank = models.ForeignKey(UserRank, on_delete=models.CASCADE, related_name='scores')  # Rank와 연결
    score = models.IntegerField()  # 점수 저장
    timestamp = models.DateTimeField(default=timezone.now)  # 시간대 저장

    def __str__(self):
        return f'{self.user_rank.rank} - {self.score} at {self.timestamp}'

class UserModel(models.Model):
    class Meta:
        db_table = "my-user"
    
    username = models.CharField(max_length=20, null=False, primary_key=True)
    password = models.CharField(max_length=256, null=False)
    password2 = models.CharField(max_length=100, null=False, default="")
    
    # UserRank와 Many-to-Many 관계 설정
    user_ranks = models.ManyToManyField(UserRank, related_name='users')
    
    # 사용자의 점수를 저장할 필드
    rank_value = models.IntegerField(null=True, blank=True)  # 점수 값, null 또는 빈 값 허용
    rank_time = models.DateTimeField(auto_now_add=True)  # 생성 시간

    def __str__(self):
        return self.username
class RankHistory(models.Model):
    class Meta:
        db_table = "my-rank_history"
    posture = models.CharField(max_length=100, null=False,default="")
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='rank_history')
    rank_value = models.IntegerField(default=0)  # 점수 저장
    timestamp = models.DateTimeField(default=timezone.now)  # 기록 시간 
    def __str__(self):
        return f'{self.user.username}  - {self.rank_value} at {self.timestamp} - {self.posture}'


class Video(models.Model):
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='videos/')
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title