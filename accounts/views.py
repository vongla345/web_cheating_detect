from datetime import datetime

from pydantic.schema import timedelta
import random
from .helpers import process_excel
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators import gzip
from django.http import StreamingHttpResponse, JsonResponse
import sqlite3
import json
import time
from datetime import datetime

from .form import TestForm, QuestionForm, ChoiceForm
from .models import Test, Question, Choice
from django.forms import formset_factory

from django.db import connection

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .form import LoginForm, RegisterForm, QuestionFormSet, ChoiceFormSet
import logging
from django.http import HttpResponse

logger = logging.getLogger('django')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT id,role_id FROM users WHERE username=? AND password=?", (username, password))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                request.session['user_id'] = user_data[0]
                if user_data[1] == 2:
                    request.session['is_teacher'] = True
                else:
                    request.session['is_teacher'] = False
                return redirect('profile')
            else:
                form.add_error('password', 'Mật khẩu không chính xác hoặc tài khoản không tồn tại.')
    else:
        form = LoginForm()

    return render(request, 'index/login.html', {'form': form})


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
                form.add_error('username', 'Username đã tồn tại.')
            else:
                form.save()
                return redirect('login')

            conn.close()
    else:
        form = RegisterForm()

    return render(request, 'index/register.html', {'form': form})


@login_required
def profile_view(request):
    user_id = request.session.get('user_id')
    logger.info(f"User ID: {user_id}")
    if not user_id:
        logger.info("User is not logged in")
        return redirect('login')

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, email, first_name, last_name, phone, date_of_birth, gender, school_name, role_id FROM users WHERE id=?",
        (user_id,))
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
        'school_name': user_data[7],
        'role_id': user_data[8]
    }

    # Render trang profile với thông tin người dùng
    return render(request, 'index/profile.html', context)


def check_session(request):
    data = request.session.items()
    if data:
        return HttpResponse(data)
    else:
        return HttpResponse('Not logged in')


def test_list(request):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    is_teacher = request.session.get('is_teacher')
    if is_teacher:
        cursor.execute("SELECT id, title, description FROM tests WHERE created_by = ?",
                       (request.session.get('user_id'),))
    else:
        cursor.execute(
            "select t.id, t.title, t.description, c.name, cu.id from tests t left join class_tests ct on t.id = ct.test_id left join class c on ct.class_id = c.id left join class_users cu on c.id = cu.class_id where cu.user_id = ? order by c.id",
            (request.session.get('user_id'),))
    tests = cursor.fetchall()
    conn.close()

    return render(request, 'test/test_list.html', {'tests': tests, 'is_teacher': is_teacher})


def create_test(request):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        'select c.id, c.name, user_id from class_users left join class c on c.id = class_users.class_id where user_id = ?',
        (request.session.get('user_id'),))
    classes = cursor.fetchall()
    if request.method == 'POST':
        test_form = TestForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')

        if test_form.is_valid() and question_formset.is_valid():
            # Lưu bài kiểm tra
            title = test_form.cleaned_data['title']
            description = test_form.cleaned_data['description']
            amount_of_time = test_form.cleaned_data['amount_of_time']
            cursor.execute("INSERT INTO tests (title, description,amount_of_time,created_by) VALUES (?, ?, ?, ?)",
                           (title, description, amount_of_time, request.session.get('user_id')))
            test_id = cursor.lastrowid

            selected_class_ids = request.POST.getlist('class_ids')  # Trả về danh sách các class_id được chọn

            # Kiểm tra danh sách các class_id
            if selected_class_ids:
                for class_id in selected_class_ids:
                    logger.info(f"Selected class ID: {class_id}")
                    cursor.execute(
                        "INSERT INTO class_tests (class_id, test_id) VALUES (?, ?)",
                        (class_id, test_id)
                    )
            else:
                logger.info("No classes selected!")

            for i, question_form in enumerate(question_formset):
                question_text = question_form.cleaned_data['question_text']
                cursor.execute("INSERT INTO questions (question_text, test_id) VALUES (?, ?)", (question_text, test_id))
                question_id = cursor.lastrowid

                # Xử lý choices cho câu hỏi
                for j in range(4):  # Mỗi câu hỏi có 4 choices
                    choice_text = request.POST.get(f'choices-{i}-{j}-choice_text')
                    is_correct = request.POST.get(f'choices-{i}-{j}-is_correct', False)
                    cursor.execute(
                        "INSERT INTO choices (choice_text, question_id, is_correct) VALUES (?, ?, ?)",
                        (choice_text, question_id, is_correct)
                    )

            conn.commit()
            conn.close()
            return redirect('test_list')

    else:
        test_form = TestForm()
        question_formset = QuestionFormSet(prefix='questions')

    conn.commit()
    conn.close()

    return render(request, 'test/create_test.html', {
        'test_form': test_form,
        'question_formset': question_formset,
        'classes': classes,
    })


def upload_test(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        try:
            # Gọi hàm xử lý file Excel
            questions = process_excel(file)
            return JsonResponse({'success': True, 'questions': questions, 'total_questions': len(questions)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


def edit_test(request, test_id):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Lấy thông tin bài kiểm tra
    cursor.execute("SELECT title, description FROM tests WHERE id = ?", (test_id,))
    test = cursor.fetchone()

    if not test:
        return HttpResponse("Test not found", status=404)

    title, description = test
    test_form = TestForm(initial={'title': title, 'description': description})

    # Lấy danh sách câu hỏi và lựa chọn
    cursor.execute("SELECT id, question_text FROM questions WHERE test_id = ?", (test_id,))
    questions = cursor.fetchall()

    # Lấy các lựa chọn cho mỗi câu hỏi
    question_data = []
    for question_id, question_text in questions:
        cursor.execute("SELECT id, choice_text, is_correct FROM choices WHERE question_id = ?", (question_id,))
        choices = cursor.fetchall()
        question_data.append({
            'id': question_id,
            'question_text': question_text,
            'choices': choices
        })

    conn.close()

    if request.method == 'POST':
        test_form = TestForm(request.POST)
        logger.info(f"Test ID: {test_id}")
        if test_form.is_valid():
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()

            # Cập nhật thông tin bài kiểm tra
            title = test_form.cleaned_data['title']
            description = test_form.cleaned_data['description']
            cursor.execute("UPDATE tests SET title = ?, description = ? WHERE id = ?", (title, description, test_id))
            # Cập nhật câu hỏi và lựa chọn
            question_count = int(request.POST.get('question_count'))
            logger.info(question_count)
            for i in range(question_count):
                question_text = request.POST.get(f'questions-{i}-question_text')
                question_id = request.POST.get(f'questions-{i}-id')

                if question_id:
                    logger.info(f"Updating question {question_id}")
                    cursor.execute("UPDATE questions SET question_text = ? WHERE id = ?", (question_text, question_id))
                else:
                    cursor.execute("INSERT INTO questions (test_id, question_text) VALUES (?, ?)",
                                   (test_id, question_text))
                    question_id = cursor.lastrowid  # Lấy ID của câu hỏi mới

                # Cập nhật hoặc thêm mới lựa chọn cho câu hỏi
                for j in range(4):  # Giới hạn 4 lựa chọn mỗi câu hỏi
                    choice_text = request.POST.get(f'choices-{i}-{j}-choice_text')
                    is_correct = request.POST.get(f'choices-{i}-{j}-is_correct', False)
                    choice_id = request.POST.get(f'choices-{i}-{j}-id', None)
                    if choice_id is not None:
                        cursor.execute(
                            "UPDATE choices SET choice_text = ?, is_correct = ? WHERE id = ?",
                            (choice_text, is_correct, choice_id)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO choices (choice_text, question_id, is_correct) VALUES (?, ?, ?)",
                            (choice_text, question_id, is_correct)
                        )

            conn.commit()
            conn.close()
            return redirect('test_list')

    return render(request, 'test/edit_test.html', {
        'test_form': test_form,
        'test_id': test_id,
        'question_data': question_data,  # Truyền danh sách câu hỏi và lựa chọn
        'question_count': len(question_data)  # Số lượng câu hỏi hiện tại
    })


def test_detail(request, test_id):
    request.session['test_id'] = test_id

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Lấy thông tin bài thi
    cursor.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    test = cursor.fetchone()

    if not test:
        return HttpResponse("<h1>Test not found</h1><p>The test you are looking for does not exist.</p>",
                            content_type="text/html")

    test_duration = test[3]  # Giả sử thời gian làm bài (phút) ở cột thứ 3
    cursor.execute('SELECT * FROM questions WHERE test_id=?', (test_id,))
    questions = cursor.fetchall()
    questions = [list(question) for question in questions]
    random.shuffle(questions)
    questions_data = []
    for question in questions:
        question_id = question[0]
        question_text = question[1]

        cursor.execute("SELECT * FROM choices WHERE question_id=?", (question_id,))
        choices = cursor.fetchall()
        choices = [list(choice) for choice in choices]

        random.shuffle(choices)

        choice_label = ['A', 'B', 'C', 'D']
        for i, choice in enumerate(choices):
            choices[i].append(choice_label[i])

        questions_data.append({
            'id': question_id,
            'question_text': question_text,
            'choices': choices
        })
    cursor.execute(
        "SELECT * FROM student_tests WHERE student_id = ? AND test_id = ? AND end_time not null ORDER BY end_time DESC",
        (request.session['user_id'], test_id))
    history_student_test = cursor.fetchall()
    history_student_test = [list(i) for i in history_student_test]
    for i in history_student_test:
        i[3] = datetime.strptime(i[3], "%Y-%m-%d %H:%M:%S.%f")
        i[3] = i[3] + timedelta(hours=7)
        i[3] = i[3].strftime("%Y/%m/%d %H:%M")

        i[4] = datetime.strptime(i[4], "%Y-%m-%d %H:%M:%S.%f")
        i[4] = i[4] + timedelta(hours=7)
        i[4] = i[4].strftime("%Y/%m/%d %H:%M")
    history_student_test = [[i[3], i[4], i[5]] for i in history_student_test]

    if request.method == 'POST':
        action = request.POST.get('action')

        # Người dùng bắt đầu bài thi
        if action == 'start_test':
            cursor.execute("INSERT INTO student_tests (student_id, test_id, start_time) VALUES (?, ?, ?)",
                           (request.session['user_id'], test_id, datetime.now()))
            conn.commit()

            # Lấy ID của lần làm bài vừa tạo
            cursor.execute("SELECT id FROM student_tests WHERE student_id = ? AND test_id = ? ORDER BY start_time DESC",
                           (request.session['user_id'], test_id))
            student_test_id = cursor.fetchone()[0]
            request.session['student_test_id'] = student_test_id

            conn.close()
            return JsonResponse({'status': 'started', 'test_duration': test_duration})

        # Người dùng nộp bài thi
        elif action == 'submit_test':
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
            cursor.execute("UPDATE student_tests SET score = ?, end_time = ? WHERE id = ?",
                           (score_db, datetime.now(), request.session['student_test_id']))
            cursor.execute("SELECT * FROM student_tests WHERE id = ?", (request.session['student_test_id'],))

            student_test = cursor.fetchone()
            student_test = list(student_test)

            student_test[3] = datetime.strptime(student_test[3], "%Y-%m-%d %H:%M:%S.%f")
            student_test[3] = student_test[3] + timedelta(hours=7)
            student_test[3] = student_test[3].strftime("%Y/%m/%d %H:%M")

            student_test[4] = datetime.strptime(student_test[4], "%Y-%m-%d %H:%M:%S.%f")
            student_test[4] = student_test[4] + timedelta(hours=7)
            student_test[4] = student_test[4].strftime("%Y/%m/%d %H:%M")

            cursor.execute("SELECT first_name, last_name FROM users WHERE id = ?", (request.session.get('user_id'),))
            student_name = cursor.fetchone()
            student_test.append(student_name[0] + ' ' + student_name[1])

            test_name = test[1]

            student_test.append(score)
            student_test.append(total_question - score)
            student_test.append(total_question)
            student_test.append(test_name)

            conn.commit()
            conn.close()

            return render(request, 'test/result.html', {'student_test': student_test, 'total_question': total_question})

    conn.close()
    return render(request, 'test/test_detail.html',
                  {'test': test, 'questions_data': questions_data, 'history_student_test': history_student_test})


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
