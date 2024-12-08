from datetime import timedelta
import random
from .helpers import process_excel
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from PIL import Image

from django.http import JsonResponse
import sqlite3
import json
from datetime import datetime

from .form import TestForm
from django.views.decorators.csrf import csrf_exempt
from .models import User, Test, Question, Choice, MonitoringData, Class, ClassTest, StudentTest, ClassUser

from .form import LoginForm, RegisterForm, QuestionFormSet
import logging
from django.http import HttpResponse

logger = logging.getLogger('django')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user_data = User.objects.filter(username=username, password=password).values_list('id', 'role_id').first()
            logger.info(f"User data: {user_data}")

            if user_data:
                request.session['user_id'] = user_data[0]
                request.session['role_id'] = user_data[1]
                return redirect('profile')
            else:
                form.add_error('password', 'Mật khẩu không chính xác hoặc tài khoản không tồn tại.')
    else:
        form = LoginForm()

    return render(request, 'index/login.html', {'form': form})


def logout_view(request):
    del request.session['user_id']
    del request.session['role_id']
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')

            user_exists = User.objects.filter(username=username).exists()

            if user_exists:
                form.add_error('username', 'Username đã tồn tại.')
            else:
                form.save()
                return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'index/register.html', {'form': form})


import os
from django.core.exceptions import ValidationError


def profile_view(request):
    user_id = request.session.get('user_id')
    logger.info(f"User ID: {user_id}")
    if not user_id:
        logger.info("User is not logged in")
        return redirect('login')

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        phone = request.POST.get('phone')
        date_of_birth = request.POST.get('birthdate')
        gender = request.POST.get('gender')
        school_name = request.POST.get('school_info')
        profile_picture = request.FILES.get('profile_picture')  # Lấy file từ form

        try:
            user = User.objects.get(id=user_id)

            # Xử lý ảnh đại diện
            if profile_picture:
                # Kiểm tra phần mở rộng
                valid_extensions = ['jpg', 'jpeg', 'png']
                file_extension = os.path.splitext(profile_picture.name)[1][1:].lower()

                if file_extension not in valid_extensions:
                    raise ValidationError(f'Định dạng file không hợp lệ: {file_extension}')

                # Lưu ảnh
                user.profile_picture.save(profile_picture.name, profile_picture)
            # Cập nhật thông tin khác
            user.phone = phone
            user.date_of_birth = date_of_birth
            user.gender = gender
            user.school_name = school_name
            user.save()

            logger.info('Thông tin đã được cập nhật thành công!')
        except ValidationError as e:
            logger.error(f"Lỗi: {e}")
            return render(request, 'index/profile.html', {'error': str(e)})
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật thông tin: {e}")
            return render(request, 'index/profile.html', {'error': 'Có lỗi xảy ra. Vui lòng thử lại.'})

        return redirect('profile')  # Load lại trang profile sau khi cập nhật

    user_data = User.objects.get(id=user_id)
    if not user_data:
        return redirect('login')
    logger.info(user_data.profile_picture)
    context = {
        'username': user_data.username,
        'email': user_data.email,
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'phone': user_data.phone,
        'date_of_birth': user_data.date_of_birth,
        'gender': user_data.gender,
        'school_name': user_data.school_name,
        'role_id': user_data.role_id,
        'profile_picture': user_data.profile_picture,
    }

    return render(request, 'index/profile.html', context)


def user_detail(request, user_id):
    logger.info(f"User ID: {user_id}")
    if not user_id:
        logger.info("User is not logged in")
        return redirect('login')

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        phone = request.POST.get('phone')
        date_of_birth = request.POST.get('birthdate')
        gender = request.POST.get('gender')
        school_name = request.POST.get('school_info')
        profile_picture = request.FILES.get('profile_picture')  # Lấy file từ form

        try:
            user = User.objects.get(id=user_id)

            # Xử lý ảnh đại diện
            if profile_picture:
                # Kiểm tra phần mở rộng
                valid_extensions = ['jpg', 'jpeg', 'png']
                file_extension = os.path.splitext(profile_picture.name)[1][1:].lower()

                if file_extension not in valid_extensions:
                    raise ValidationError(f'Định dạng file không hợp lệ: {file_extension}')

                # Lưu ảnh
                user.profile_picture.save(profile_picture.name, profile_picture)
            # Cập nhật thông tin khác
            user.phone = phone
            user.date_of_birth = date_of_birth
            user.gender = gender
            user.school_name = school_name
            user.save()

            logger.info('Thông tin đã được cập nhật thành công!')
        except ValidationError as e:
            logger.error(f"Lỗi: {e}")
            return render(request, 'index/profile.html', {'error': str(e)})
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật thông tin: {e}")
            return render(request, 'index/profile.html', {'error': 'Có lỗi xảy ra. Vui lòng thử lại.'})

        return redirect('profile')  # Load lại trang profile sau khi cập nhật

    user_data = User.objects.get(id=user_id)
    if not user_data:
        return redirect('login')
    logger.info(user_data.profile_picture)
    context = {
        'username': user_data.username,
        'email': user_data.email,
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'phone': user_data.phone,
        'date_of_birth': user_data.date_of_birth,
        'gender': user_data.gender,
        'school_name': user_data.school_name,
        'role_id': user_data.role_id,
        'profile_picture': user_data.profile_picture,
    }

    return render(request, 'index/profile.html', context)


def delete_user(request, user_id):
    if request.method == 'POST':  # Chỉ chấp nhận phương thức POST
        try:
            user = get_object_or_404(User, id=user_id)
            user.delete()  # Xóa user khỏi cơ sở dữ liệu
            return JsonResponse({'success': True, 'message': 'Người dùng đã được xóa thành công!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'})


def check_session(request):
    data = request.session.items()
    if data:
        return HttpResponse(data)
    else:
        return HttpResponse('Not logged in')


def user_list(request):
    # Lấy từ khóa tìm kiếm từ request (GET parameter)
    search_query = request.GET.get('search', '')

    # Lấy toàn bộ danh sách người dùng, áp dụng tìm kiếm nếu có
    users = User.objects.filter(
        Q(username__icontains=search_query) |
        Q(first_name__icontains=search_query) |
        Q(last_name__icontains=search_query) |
        Q(email__icontains=search_query) |
        Q(phone__icontains=search_query)
    ).values_list('id', 'username', 'first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth', 'role_id')

    # Xử lý dữ liệu người dùng
    users = [list(i) for i in users]
    for i in users:
        # Gộp họ và tên
        if i[2] is not None and i[3] is not None:
            i[2] = i[2] + ' ' + i[3]
        i.pop(3)

        # Xử lý giới tính
        if i[5] is not None:
            i[5] = 'Nam' if i[5] == 1 else 'Nữ'

        # Xử lý loại tài khoản
        if i[7] == 1:
            i[7] = 'Học sinh'
        elif i[7] == 2:
            i[7] = 'Giáo viên'
        else:
            i[7] = 'Quản trị viên'

    # Xử lý các giá trị None
    for user in users:
        user[:] = [value if value is not None else '' for value in user]

    # Phân trang
    items_per_page = 10
    page_number = request.GET.get('page', 1)
    paginator = Paginator(users, items_per_page)

    try:
        # Lấy trang hiện tại
        page_obj = paginator.get_page(page_number)
    except EmptyPage:
        # Nếu trang vượt quá giới hạn, trả về trang cuối cùng
        page_obj = paginator.get_page(paginator.num_pages)

    # Trả về dữ liệu cho template
    return render(request, 'user/user_list.html', {
        'users': page_obj.object_list,  # Danh sách người dùng trên trang hiện tại
        'page_obj': page_obj,  # Đối tượng phân trang
        'search_query': search_query  # Từ khóa tìm kiếm (để hiển thị lại)
    })


def test_list(request):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    role_id = request.session.get('role_id')
    if role_id == 2:
        tests = Test.objects.filter(created_by=request.session.get('user_id')).values_list('id', 'title', 'description')
    elif role_id == 1:
        cursor.execute(
            "select t.id, t.title, t.description, c.name, cu.id from tests t left join class_tests ct on t.id = ct.test_id left join class c on ct.class_id = c.id left join class_users cu on c.id = cu.class_id where cu.user_id = ? order by c.id",
            (request.session.get('user_id'),))
        tests = cursor.fetchall()
        conn.close()

    return render(request, 'test/test_list.html', {'tests': tests, 'role_id': 'role_id'})


def create_test(request):
    classes = ClassUser.objects.prefetch_related('class_id').filter(user_id=request.session.get('user_id')).values_list(
        'class_id__id', 'class_id__name')

    if request.method == 'POST':
        test_form = TestForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')

        if test_form.is_valid() and question_formset.is_valid():
            title = test_form.cleaned_data['title']
            description = test_form.cleaned_data['description']
            amount_of_time = test_form.cleaned_data['amount_of_time']

            test = Test(title=title, description=description, amount_of_time=amount_of_time,
                        created_by_id=request.session.get('user_id'))
            test.save()
            test_id = test.id

            selected_class_ids = request.POST.getlist('class_ids')

            if selected_class_ids:
                for class_id in selected_class_ids:
                    selected_class = Class.objects.filter(id=class_id).first()
                    class_test = ClassTest(class_id=selected_class, test=test)
                    class_test.save()
            else:
                logger.info("No classes selected!")

            for i, question_form in enumerate(question_formset):
                question_text = question_form.cleaned_data['question_text']
                question = Question(question_text=question_text, test_id=test_id)
                question.save()
                question_id = question.id

                for j in range(4):
                    choice_text = request.POST.get(f'choices-{i}-{j}-choice_text')
                    is_correct = request.POST.get(f'choices-{i}-{j}-is_correct') == 'on'

                    choice = Choice(choice_text=choice_text, question_id=question_id, is_correct=is_correct)
                    choice.save()

            return redirect('test_list')

    else:
        test_form = TestForm()
        question_formset = QuestionFormSet(prefix='questions')

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

    test = Test.objects.filter(id=test_id).values_list('title', 'description', 'amount_of_time').first()

    if not test:
        return HttpResponse("Test not found", status=404)

    title, description, amount_of_time = test
    test_form = TestForm(initial={'title': title, 'description': description, 'amount_of_time': amount_of_time})

    questions = Question.objects.filter(test_id=test_id).values_list('id', 'question_text').values_list('id',
                                                                                                        'question_text')

    classes = ClassUser.objects.prefetch_related('class_id').filter(user_id=request.session.get('user_id')).values_list(
        'class_id__id', 'class_id__name')
    classes = [list(i) for i in classes]

    selected_classes = ClassTest.objects.prefetch_related('class_id').filter(test_id=test_id).values_list(
        'class_id__id')
    selected_classes = [i[0] for i in selected_classes]

    for class_item in classes:
        if class_item[0] in selected_classes:
            class_item.append(True)
        else:
            class_item.append(False)

    question_data = []
    for question_id, question_text in questions:
        choices = Choice.objects.filter(question_id=question_id).values_list('id', 'choice_text', 'is_correct')
        question_data.append({
            'id': question_id,
            'question_text': question_text,
            'choices': choices,
        })

    if request.method == 'POST':
        if request.POST.get('action') == 'delete':

            test = Test.objects.filter(id=test_id).first()
            test.delete()

            return redirect('test_list')
        elif request.POST.get('action') == 'update':
            test_form = TestForm(request.POST)
            if test_form.is_valid():
                conn = sqlite3.connect('db.sqlite3')
                cursor = conn.cursor()

                test = Test.objects.filter(id=test_id).first()
                test.title = test_form.cleaned_data['title']
                test.description = test_form.cleaned_data['description']
                test.amount_of_time = test_form.cleaned_data['amount_of_time']
                test.save()

                selected_class_ids = request.POST.getlist('class_ids')  # Lấy danh sách ID của các lớp đã chọn

                selected_class_ids = [int(i) for i in selected_class_ids]

                class_test = ClassTest.objects.filter(test_id=test_id)
                class_test.delete()

                if selected_class_ids:
                    for class_id in selected_class_ids:
                        selected_class = Class.objects.filter(id=class_id).first()
                        class_test = ClassTest(test=test, class_id=selected_class)
                        class_test.save()
                else:
                    logger.info("No classes selected!")

                # Cập nhật câu hỏi và lựa chọn
                question_count = int(request.POST.get('question_count'))

                questions = Question.objects.filter(test_id=test_id)
                for question in questions:
                    choices = Choice.objects.filter(question_id=question.id)
                    choices.delete()
                questions.delete()

                for i in range(question_count):
                    question_text = request.POST.get(f'questions-{i}-question_text')
                    # question_id = request.POST.get(f'questions-{i}-id')

                    question = Question(test_id=test_id, question_text=question_text)
                    question.save()
                    question_id = question.id  # Lấy ID của câu hỏi mới

                    # Thêm mới lại các câu hỏi
                    for j in range(4):  # Giới hạn 4 lựa chọn mỗi câu hỏi
                        choice_text = request.POST.get(f'choices-{i}-{j}-choice_text')
                        is_correct = request.POST.get(f'choices-{i}-{j}-is_correct', False)
                        choice_id = request.POST.get(f'choices-{i}-{j}-id', None)
                        if is_correct:
                            is_correct = True
                        choice = Choice(question_id=question_id, choice_text=choice_text, is_correct=is_correct)
                        choice.save()

                return redirect('test_list')

    return render(request, 'test/edit_test.html', {
        'test_form': test_form,
        'test_id': test_id,
        'question_data': question_data,  # Truyền danh sách câu hỏi và lựa chọn
        'question_count': len(question_data),  # Số lượng câu hỏi hiện tại
        'classes': classes,
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

    cursor.execute("select profile_picture from users where id = ?", (request.session.get('user_id'),))
    profile_picture = cursor.fetchone()
    profile_picture = profile_picture[0]
    logger.info(profile_picture)
    test_duration = test[3]
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

    cursor.execute('select first_name, last_name from main.users where id = ?', (request.session.get('user_id'),))
    name = cursor.fetchone()
    name = name[0] + ' ' + name[1]
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
                  {'name': name, 'test': test, 'questions_data': questions_data,
                   'history_student_test': history_student_test,
                   'profile_picture': profile_picture})


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

            # Extract data
            dominant_class = data.get('dominantClass')
            logger.info(f"dominant_class: {dominant_class}")
            cheating_duration = data.get('cheatingDuration', 0)
            logger.info(f"cheating_duration: {cheating_duration}")
            switch_count = data.get('switchCount', 0)
            logger.info(f"switch_count: {switch_count}")

            # Determine the status
            if dominant_class == "Cheating":
                status = "Cheating"
            else:
                status = "Normal"

            # Log the status
            logger.info(f"Status: {status}, Cheating Duration: {cheating_duration}s, Switch Count: {switch_count}")

            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("""
                    INSERT INTO monitoring_data (student_test_id, timestamp, status, cheating_duration, switch_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_test_id, datetime.now(), status, cheating_duration, switch_count))
            conn.commit()
            conn.close()
            # Send Telegram notification if cheating is detected
            # if status == "Cheating":
            # send_telegram_notification(student_test_id, cheating_duration)
            return JsonResponse({'status': 'success'})

        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return JsonResponse({'status': 'failed', 'message': str(e)})


def class_list(request):
    role_id = request.session.get('role_id')
    if role_id == 2:
        classes = ClassUser.objects.select_related('class_id__school_year').filter(
            user=request.session.get('user_id')).values_list('class_id__id', 'class_id__name',
                                                             'class_id__school_year__name')
    elif role_id == 3:
        classes = Class.objects.prefetch_related('school_year').values_list('id', 'name', 'school_year__name')
    else:
        classes = []

    logger.info(f"Classes: {classes}")

    return render(request, 'class/class_list.html', {'classes': classes})


def class_detail(request, class_id):
    student_list = ClassUser.objects.prefetch_related('user').filter(class_id=class_id, user__role=1).values_list(
        'user__id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    logger.info(f"Students: {student_list}")

    return render(request, 'class/class_detail.html', {'students': student_list})
