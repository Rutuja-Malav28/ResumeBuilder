from rest_framework.response import Response
from bson.errors import InvalidId
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from rest_framework import status
from .mongo import get_db
from bson.objectid import ObjectId
import bcrypt
import random
from django.core.mail import send_mail
import uuid

current_user = None

@api_view(['POST'])
def register_user(request):
    db = get_db()
    register_collection = db['register']

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return JsonResponse({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if register_collection.find_one({"email": email}):
        return JsonResponse({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user_data = {
        "user_id": str(uuid.uuid4()),  # Generate a unique user ID
        "username": username,
        "email": email,
        "password": hashed_password
    }

    register_collection.insert_one(user_data)
    return JsonResponse({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_user(request):
    global current_user  

    db = get_db()
    register_collection = db['register']

    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return JsonResponse({"error": "Email and password are required."}, status=400)

    user = register_collection.find_one({"email": email})

    if not user:
        return JsonResponse({"error": "Invalid email or password."}, status=401)

    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return JsonResponse({"error": "Invalid email or password."}, status=401)

    current_user = user

    return JsonResponse({"message": "Login successful.", "user": {"user_id": user['user_id']}}, status=200)

@api_view(['POST'])
def forgot_user(request):
    db = get_db()
    register_collection = db['register']

    email = request.data.get('email')

    if not email:
        return JsonResponse({"error": "Email id is required."}, status=status.HTTP_400_BAD_REQUEST)

    user = register_collection.find_one({"email": email})

    if not user:
        return JsonResponse({"message": "If this email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

    try:
        otp = random.randint(100000, 999999)
        expiration_time = datetime.utcnow() + timedelta(minutes=5)

        register_collection.update_one(
            {"email": email},
            {"$set": {"otp": otp, "otp_expiration": expiration_time}}
        )

        subject = "Your OTP for Password Reset"
        message = f"Your OTP for resetting your password is: {otp}"

        send_mail(subject, message, 'demo28may2001@gmail.com', [email])
        return JsonResponse({"message": "OTP has been sent to your email."}, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error occurred:", e)
        return JsonResponse({"error": "Error sending email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_otp(request):
    db = get_db()
    register_collection = db['register']
    
    email = request.data.get('email')
    otp = request.data.get('otp')

    if not email or not otp:
        return JsonResponse({"error": "Email and OTP are required."}, status=400)

    user = register_collection.find_one({"email": email})

    if not user or 'otp' not in user:
        return JsonResponse({"error": "Invalid email or OTP."}, status=400)

    if user['otp'] != otp:
        return JsonResponse({"error": "Invalid OTP."}, status=400)

    if datetime.utcnow() > user['otp_expiration']:
        return JsonResponse({"error": "OTP has expired."}, status=400)

    return JsonResponse({"message": "Verification successful."}, status=200)

@api_view(['POST'])
def change_password(request):
    db = get_db()
    register_collection = db['register']
    
    email = request.data.get('email')
    new_password = request.data.get('new_password')

    if not email or not new_password:
        return JsonResponse({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = register_collection.find_one({"email": email})
    if not user:
        return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    register_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )

    return JsonResponse({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_all_users(request):
    global current_user  

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    register_collection = db['register']

    user = register_collection.find_one({"user_id": current_user.get('user_id')})

    if not user:
        return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    user['_id'] = str(user['_id'])  # Convert ObjectId to string
    user.pop('password', None)  # Remove password from response

    return JsonResponse(user, status=status.HTTP_200_OK)

from bson import ObjectId  # Import ObjectId for generating unique IDs

@api_view(['POST'])
def submit_resume(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=401)

    db = get_db()
    resume_collection = db['resumes']
    experience_collection = db['experiences']  # Collection for experiences
    education_collection = db['educations']      # Collection for education
    skills_collection = db['skills']            # Collection for skills

    resume_title = request.data.get('resume_title')
    objective = request.data.get('objective')
    full_name = request.data.get('full_name')
    email = request.data.get('email')
    mobile_no = request.data.get('mobile_no')
    dob = request.data.get('dob')
    gender = request.data.get('gender')
    nationality = request.data.get('nationality')
    hobbies = request.data.get('hobbies')
    languages_known = request.data.get('languages_known')
    address = request.data.get('address')

    if not resume_title or not objective or not full_name or not mobile_no or not dob or not gender or not nationality or not address:
        return JsonResponse({"error": "All fields are required."}, status=400)

    # Create a unique resume_id
    resume_id = str(ObjectId())

    # Fetch experiences, education, and skills for the user
    experiences = list(experience_collection.find({"user_id": current_user['user_id']}))
    educations = list(education_collection.find({"user_id": current_user['user_id']}))
    skills = list(skills_collection.find({"user_id": current_user['user_id']}))

    # Convert ObjectId to string for experiences, education, and skills
    for experience in experiences:
        experience['_id'] = str(experience['_id'])
        
    for edu in educations:
        edu['_id'] = str(edu['_id'])

    for skill in skills:
        skill['_id'] = str(skill['_id'])

    resume_data = {
        "resume_id": resume_id,  # Add the unique resume_id
        "resume_title": resume_title,
        "objective": objective,
        "full_name": full_name,
        "mobile_no": mobile_no,
        "email":email,
        "dob": dob,
        "gender": gender,
        "nationality": nationality,
        "hobbies": hobbies,
        "languages_known": languages_known,
        "address": address,
        "user_id": current_user['user_id'],  # Use user ID instead of email
        "created_at": datetime.utcnow(),
        "experiences": experiences,  # Add experiences
        "educations": educations,      # Add education
        "skills": skills             # Add skills
    }

    resume_collection.insert_one(resume_data)

    return JsonResponse({"message": "Resume submitted successfully.", "resume_id": resume_id}, status=201)

@api_view(['POST'])
def submit_experience(request):
    global current_user  

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=401)

    db = get_db()
    experience_collection = db['experiences']

    job_title = request.data.get('jobTitle')
    company_name = request.data.get('companyName')
    start_date = request.data.get('startDate')
    end_date = request.data.get('endDate')
    description = request.data.get('description')

    if not job_title or not company_name or not start_date or not description:
        return JsonResponse({"error": "All fields except End Date are required."}, status=400)

    experience_data = {
        "job_title": job_title,
        "company_name": company_name,
        "start_date": datetime.strptime(start_date, '%Y-%m-%d'),
        "end_date": datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
        "description": description,
        "user_id": current_user['user_id'],  # Use user ID instead of email
        "created_at": datetime.utcnow()
    }

    experience_collection.insert_one(experience_data)

    return JsonResponse({"message": "Experience submitted successfully."}, status=201)

@api_view(['POST'])
def submit_education(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=401)

    db = get_db()
    education_collection = db['educations']

    institution_name = request.data.get('institutionName')
    degree = request.data.get('degree')
    field_of_study = request.data.get('fieldOfStudy')
    start_date = request.data.get('startDate')
    graduation_date = request.data.get('graduationDate')
    honors = request.data.get('honors')
    coursework = request.data.get('coursework')

    if not institution_name or not degree or not start_date:
        return JsonResponse({"error": "Institution Name, Degree, and Start Date are required."}, status=400)

    education_data = {
        "institution_name": institution_name,
        "degree": degree,
        "field_of_study": field_of_study,
        "start_date": datetime.strptime(start_date, '%Y-%m'),
        "graduation_date": datetime.strptime(graduation_date, '%Y-%m') if graduation_date else None,
        "honors": honors,
        "coursework": coursework,
        "user_id": current_user['user_id'],  # Use user ID instead of email
        "created_at": datetime.utcnow()
    }

    education_collection.insert_one(education_data)

    return JsonResponse({"message": "Education submitted successfully."}, status=201)

@api_view(['POST'])
def submit_skill(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=401)

    db = get_db()
    skill_collection = db['skills']

    skill = request.data.get('skills')
    skillLevel = request.data.get('skillLevel')

    if not skill:
        return JsonResponse({"error": "Skills should not be empty"}, status=400)

    skill_data = {
        "skill": skill,
        "skillLevel": skillLevel,
        "user_id": current_user['user_id'],
        "created_at": datetime.utcnow()
    }

    try:
        skill_collection.insert_one(skill_data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Skill submitted successfully."}, status=201)



@api_view(['GET'])
def get_user_experiences(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    experience_collection = db['experiences']

    experiences = list(experience_collection.find({"user_id": current_user['user_id']}))

    for experience in experiences:
        experience['_id'] = str(experience['_id'])

    return JsonResponse(experiences, safe=False, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_user_educations(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    education_collection = db['educations']

    educations = list(education_collection.find({"user_id": current_user['user_id']}))

    for education in educations:
        education['_id'] = str(education['_id'])

    return JsonResponse(educations, safe=False, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_user_skills(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    skill_collection = db['skills']

    skills = list(skill_collection.find({"user_id": current_user['user_id']}))

    for skill in skills:
        skill['_id'] = str(skill['_id'])

    return JsonResponse(skills, safe=False, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_experience(request, id):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    experience_collection = db['experiences']

    # Attempt to delete the experience
    result = experience_collection.delete_one({"_id": ObjectId(id), "user_id": current_user['user_id']})

    if result.deleted_count == 1:
        return JsonResponse({"message": "Experience deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    else:
        return JsonResponse({"error": "Experience not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['DELETE'])
def delete_education(request, id):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    education_collection = db['educations']

    # Attempt to delete the experience
    result = education_collection.delete_one({"_id": ObjectId(id), "user_id": current_user['user_id']})

    if result.deleted_count == 1:
        return JsonResponse({"message": "Experience deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    else:
        return JsonResponse({"error": "Experience not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(['DELETE'])
def delete_skill(request, id):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    skill_collection = db['skills']

    # Attempt to delete the experience
    result = skill_collection.delete_one({"_id": ObjectId(id), "user_id": current_user['user_id']})

    if result.deleted_count == 1:
        return JsonResponse({"message": "Experience deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    else:
        return JsonResponse({"error": "Experience not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_resume(request, id):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    resume_collection = db['resumes']

    # Attempt to delete the experience
    result = resume_collection.delete_one({"_id": ObjectId(id), "user_id": current_user['user_id']})

    if result.deleted_count == 1:
        return JsonResponse({"message": "Resume deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    else:
        return JsonResponse({"error": "Resume not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_user_resumes(request):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    resume_collection = db['resumes']

    resumes = list(resume_collection.find({"user_id": current_user['user_id']}))

    for resume in resumes:
        resume['_id'] = str(resume['_id'])

    return JsonResponse(resumes, safe=False, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_resume_by_id(request, id):
    global current_user

    if not current_user:
        return JsonResponse({"error": "Unauthorized access. Please log in."}, status=status.HTTP_401_UNAUTHORIZED)

    db = get_db()
    resume_collection = db['resumes']

    resume = resume_collection.find_one({"_id": ObjectId(id), "user_id": current_user['user_id']})

    if not resume:
        return JsonResponse({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

    resume['_id'] = str(resume['_id'])

    return JsonResponse(resume, status=status.HTTP_200_OK)


@api_view(['POST'])
def logout_user(request):
    global current_user

    # Set current_user to None to log out
    current_user = None

    return JsonResponse({"message": "Logout successful."}, status=status.HTTP_200_OK)
