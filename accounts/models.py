from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username

class Test(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1)  # A, B, C, or D

    def __str__(self):
        return self.question_text

class Choice(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    user = models.CharField(max_length=100)  # Hoặc sử dụng mô hình User của Django
    score = models.IntegerField()

    def __str__(self):
        return f"{self.user} - {self.score}"


