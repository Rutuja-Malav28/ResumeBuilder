# users/urls.py
from django.urls import path
from .views import delete_education, delete_experience, delete_resume, delete_skill, get_all_users, get_resume_by_id, get_user_educations, get_user_experiences, get_user_resumes, get_user_skills, login_user, logout_user, register_user, forgot_user, submit_education, submit_experience, submit_resume, submit_skill, verify_otp,change_password

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path('forgotpassword/',forgot_user, name='forgot_user'),
    path('verifyotp/',verify_otp, name='verify_otp'),
    path('changepassword/',change_password,name='change_password'),
    path('get_all_users/',get_all_users,name= 'get_all_users'),
    path('submit_experience/',submit_experience,name='submit_experience'),
    path('submit_education/',submit_education,name='submit_education'),
    path('submit_skill/',submit_skill,name='submit_skill'),
    path('get_user_experiences/',get_user_experiences, name='get_user_experiences'),
    path('get_user_educations/',get_user_educations,name='get_user_educations'),
    path('get_user_skills/',get_user_skills,name='get_user_skills'),
    path('submit_resume/',submit_resume,name="submit_resume"),
    path('get_user_resumes/',get_user_resumes, name='get_user_resumes'),
    path('experiences/<str:id>/', delete_experience, name='delete_experience'),
    path('educations/<str:id>/', delete_education, name='delete_education'),
    path('skills/<str:id>/', delete_skill, name='delete_skill'),
    path('resume/<str:id>/', delete_resume, name='delete_resume'),
    path('resumes/<str:id>/', get_resume_by_id, name='get_resume_by_id'),
    path('logout/', logout_user, name='logout_user'),
]
