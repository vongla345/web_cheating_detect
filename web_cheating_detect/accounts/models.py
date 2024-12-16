from django.db import models
from pyarrow import nulls


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.BooleanField(blank=True, null=True)  # True: Male, False: Female
    school_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='users', default=1)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    class Meta:
        db_table = 'users'  # Ánh xạ đến bảng `users`

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'roles'

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount_of_time = models.IntegerField()
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tests',db_column='created_by',null=True)
    attempt_limit = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tests'

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    question_text = models.CharField(max_length=255)
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='questions',db_column='test_id')

    class Meta:
        db_table = 'questions'

class Choice(models.Model):
    id = models.AutoField(primary_key=True)
    choice_text = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='choices',db_column='question_id')

    class Meta:
        db_table = 'choices'

class StudentTest(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='student_tests',db_column='student_id')
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='student_tests',db_column='test_id')
    score = models.FloatField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'student_tests'

class MonitoringData(models.Model):
    id = models.AutoField(primary_key=True)
    student_test = models.ForeignKey('StudentTest', on_delete=models.CASCADE, related_name='monitoring_data',db_column='student_test_id')
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=255)
    cheating_duration = models.IntegerField(blank=True, null=True)
    switch_count = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'monitoring_data'

class SchoolYear(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'school_year'

class Class (models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    school_year = models.ForeignKey('SchoolYear', on_delete=models.CASCADE, related_name='classes',db_column='school_year_id')
    class Meta:
        db_table = 'class'

class ClassUser(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='class_users',db_column='user_id')
    class_id = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='class_users',db_column='class_id')
    class Meta:
        db_table = 'class_users'
class ClassTest(models.Model):
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='class_tests',db_column='test_id')
    class_id = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='class_tests',db_column='class_id')
    class Meta:
        db_table = 'class_tests'