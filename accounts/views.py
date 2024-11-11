from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators import gzip
from django.http import StreamingHttpResponse, JsonResponse
import sqlite3
import json
import time

from spyder.plugins.completion.providers.kite.utils.status import status
from sympy.stats.rv import probability
from tensorflow.python.ops.weak_tensor_ops import operator

time.strftime('%Y-%m-%d %H:%M:%S')

from django.db import connection


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .form import LoginForm, RegisterForm
import logging
from django.http import HttpResponse

logger = logging.getLogger('django')
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            logger.info('Login form is valid')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                logger.info('Login successful')
                request.session['user_id'] = user_data[0]
                return redirect('profile')
            else:
                logger.error(request, 'Login failed. Please check your username and password.')
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})
def logout_view(request):
    del request.session['user_id']
    return redirect('login')
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')

            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user_exists = cursor.fetchone()

            if user_exists:
                messages.error(request, 'Username already exists. Please choose a different one.')
            else:
                form.save()
                messages.success(request, 'Your account has been created! You can now log in.')
                return redirect('login')

            conn.close()
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})
@login_required
def profile_view(request):
    user_id = request.session.get('user_id')
    logger.info(f"User ID: {user_id}")
    if not user_id:
        logger.info("User is not logged in")
        return redirect('login')

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, first_name, last_name, phone, date_of_birth, gender, school_name FROM users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return redirect('login')

    context = {
        'username': user_data[0],
        'email': user_data[1],
        'first_name': user_data[2],
        'last_name': user_data[3],
        'phone': user_data[4],
        'date_of_birth': user_data[5],
        'gender': user_data[6],
        'school_name': user_data[7]
    }

    # Render trang profile với thông tin người dùng
    return render(request, 'registration/profile.html', context)

def check_session(request):
    data = request.session.items()
    if data:
        return HttpResponse(data)
    else:
        return HttpResponse('Not logged in')

def test_list(request):
    conn  = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tests")
    tests = cursor.fetchall()
    conn.close()

    return render(request, 'test/test_list.html', {'tests': tests})
def test_detail(request, test_id):
    request.session['test_id'] = test_id

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    test = cursor.fetchone()

    if not test:
        return HttpResponse("<h1>Test not found</h1><p>The test you are looking for does not exist.</p>", content_type="text/html")

    cursor.execute('SELECT * FROM questions WHERE test_id=?', (test_id,))
    questions = cursor.fetchall()

    questions_data = []
    for question in questions:
        question_id = question[0]
        question_text = question[1]

        cursor.execute("SELECT * FROM choices WHERE question_id=?", (question_id,))
        choices = cursor.fetchall()

        questions_data.append({
            'id': question_id,
            'question_text': question_text,
            'choices': choices
        })


    if request.method == 'POST':
        del request.session['test_id']
        total_question = len(questions_data)
        score = 0

        for question in questions_data:
            question_id = str(question['id'])
            correct_answer = next((choice[0] for choice in question['choices'] if choice[3]), None)
            user_answer = request.POST.get(question_id)

            if user_answer and int(user_answer) == correct_answer:
                score += 1
        score_db = (score / total_question) * 10
        logger.info('Finish Test')
        cursor.execute("UPDATE student_tests SET score = ?, end_time = ? where id = ? ", (score_db,datetime.now(), request.session['student_test_id']))
        conn.commit()
        conn.close()

        return render(request, 'test/result.html', {'score': score, 'total_question': total_question})

    cursor.execute("INSERT INTO student_tests (student_id, test_id, start_time) VALUES (?, ?, ?)", (request.session['user_id'], test_id, datetime.now()))
    conn.commit()

    cursor.execute("SELECT id FROM student_tests WHERE student_id = ? AND test_id = ? ORDER BY start_time DESC", (request.session['user_id'], test_id))
    student_test_id = cursor.fetchone()[0]
    request.session['student_test_id'] = student_test_id

    conn.close()
    return render(request, 'test/test_detail.html', {'test': test, 'questions_data': questions_data})


import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection

# Create a logger
logger = logging.getLogger(__name__)

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection

# Create a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def save_prediction(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            logger.info("Received data: %s", data)

            # Check if student_test_id is in session
            student_test_id = request.session.get('student_test_id')
            if not student_test_id:
                logger.error("student_test_id not found in session")
                return JsonResponse({'status': 'failed', 'message': 'student_test_id is missing in session'})

            # Find the item with the highest probability
            max_item = max(data, key=lambda x: float(x['probability']))  # Ensure probability is a float
            status = max_item['className']
            probability = float(max_item['probability'])  # Ensure probability is a float

            # Update status if not "Normal"
            if status != 'Normal':
                status = 'Cheating'

            # Log the status and probability
            logger.info(f"Status: {status}, Probability: {probability}")

            # Insert data into the monitoring_data table
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO monitoring_data (student_test_id, timestamp, status, probability)
                    VALUES (?, ?, ?, ?)
                """, [student_test_id, datetime.now(), status, probability])

            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON")
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON format'})
        except KeyError as e:
            logger.error(f"Missing key: {str(e)}")
            return JsonResponse({'status': 'failed', 'message': f'Missing key: {str(e)}'})
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return JsonResponse({'status': 'failed', 'message': str(e)})

    return JsonResponse({'status': 'failed', 'message': 'Only POST requests allowed'})


