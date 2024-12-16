from django.contrib import admin
from .models import User, Role, Test, Question, Choice, StudentTest, MonitoringData, Class, ClassUser, ClassTest, SchoolYear
# Register your models here.

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(StudentTest)
admin.site.register(MonitoringData)
admin.site.register(Class)
admin.site.register(ClassUser)
admin.site.register(ClassTest)
admin.site.register(SchoolYear)

