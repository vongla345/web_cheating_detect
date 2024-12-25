from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic.base import RedirectView

urlpatterns = ([
    path('', RedirectView.as_view(url='/login/', permanent=False)),  # Redirect to /login/
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('check_session/', views.check_session, name='check_session'),
    path('user_list/', views.user_list, name='user_list'),
    path('user_detail/<int:user_id>/', views.user_detail, name='user_detail'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('test/', views.test_list, name='test_list'),
    path('create_test/', views.create_test, name='create_test'),
    path('edit_test/<int:test_id>/', views.edit_test, name='edit_test'),
    path('upload_test/', views.upload_test, name='upload_test'),
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),
    path('save_prediction/', views.save_prediction, name='save_prediction'),
    path('class_list/', views.class_list, name='class_list'),
    path('create_class/', views.create_class, name='create_class'),
    path('upload_student_file/', views.upload_student_file, name='upload_student_file'),
    path ('delete_class/<int:class_id>/', views.delete_class, name='delete_class'),
    path('class_detail/<int:class_id>/', views.class_detail, name='class_detail'),
    path('get_user_info/<int:user_id>/', views.get_user_info, name='get_user_info'),
    path('class_detail/<int:class_id>/add_student/', views.add_student_class, name='add_student'),
    path('class_detail/<int:class_id>/delete_student/', views.delete_student_class, name='delete_student'),

])

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
