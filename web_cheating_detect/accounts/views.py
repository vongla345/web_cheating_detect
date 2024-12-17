from datetime import timedelta
import random
import pandas as pd

from .helpers import process_excel
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

from django.http import JsonResponse
import sqlite3
import json
from datetime import datetime

from .form import TestForm
from django.views.decorators.csrf import csrf_exempt
from .models import User, Test, Question, Choice, MonitoringData, Class, ClassTest, StudentTest, ClassUser, SchoolYear

from .form import LoginForm, RegisterForm, QuestionFormSet
import logging
from django.http import HttpResponse
import os
from django.conf import settings

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

                # Xóa ảnh cũ nếu có
                if user.profile_picture:
                    old_picture_path = user.profile_picture.path
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)  # Xóa ảnh cũ

                # Lưu ảnh mới
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

    # load danh sách lớp của người dùng và giáo viên chủ nhiệm tương ứng
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT c.id AS class_id, c.name AS class_name, sy.name AS school_year_name, u.first_name AS teacher_first_name, u.last_name AS teacher_last_name FROM class_users cu_student LEFT JOIN class c ON c.id = cu_student.class_id LEFT JOIN school_year sy ON c.school_year_id = sy.id LEFT JOIN class_users cu_teacher ON cu_teacher.class_id = c.id LEFT JOIN users u ON cu_teacher.user_id = u.id WHERE cu_student.user_id = ? AND u.role_id = 2', (user_id,))
    user_class = cursor.fetchall()

    logger.info(user_class)

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
        'user_class': user_class
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

    if user_data.role_id == 1:
        # load danh sách lớp của người dùng và giáo viên chủ nhiệm tương ứng
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT  c.id AS class_id, c.name AS class_name, sy.name AS school_year_name, u.first_name AS teacher_first_name, u.last_name AS teacher_last_name FROM class_users cu_student LEFT JOIN class c ON c.id = cu_student.class_id LEFT JOIN school_year sy ON c.school_year_id = sy.id LEFT JOIN class_users cu_teacher ON cu_teacher.class_id = c.id LEFT JOIN  users u ON cu_teacher.user_id = u.id WHERE cu_student.user_id = ? AND u.role_id = 2',
            (user_id,))
        user_class = cursor.fetchall()
        conn.close()
    elif user_data.role_id == 2:
        user_class = ClassUser.objects.select_related('class_id__school_year').filter(
            user=user_id
        ).values_list('class_id__id', 'class_id__name', 'class_id__school_year__name')
    else:
        user_class = []
    logger.info(user_data.role_id)
    logger.info(user_class)

    context = {
        'username': user_data.username,
        'email': user_data.email,
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'phone': user_data.phone,
        'date_of_birth': user_data.date_of_birth,
        'gender': user_data.gender,
        'school_name': user_data.school_name,
        'role_id_user': user_data.role_id,
        'profile_picture': user_data.profile_picture,
        'role_id': request.session.get('role_id'),
        'user_class': user_class
    }

    return render(request, 'user/user_detail.html', context)


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
        'role_id': request.session.get('role_id'),  # ID của loại tài khoản
        'users': page_obj.object_list,  # Danh sách người dùng trên trang hiện tại
        'page_obj': page_obj,  # Đối tượng phân trang
        'search_query': search_query  # Từ khóa tìm kiếm (để hiển thị lại)
    })


def test_list(request):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    role_id = request.session.get('role_id')
    if role_id == 1:
        cursor.execute(
            "select t.id, t.title, t.description, c.name, cu.id from tests t left join class_tests ct on t.id = ct.test_id left join class c on ct.class_id = c.id left join class_users cu on c.id = cu.class_id where cu.user_id = ? order by c.id",
            (request.session.get('user_id'),))
        tests = cursor.fetchall()
        conn.close()
    else:
        tests = Test.objects.filter(created_by=request.session.get('user_id')).values_list('id', 'title', 'description')

    return render(request, 'test/test_list.html', {
        'tests': tests,
        'role_id': role_id
    })


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
            attempt_limit = test_form.cleaned_data['attempt_limit']

            test = Test(title=title, description=description, amount_of_time=amount_of_time,
                        attempt_limit=attempt_limit,
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
        'role_id': request.session.get('role_id'),
        'test_form': test_form,
        'question_formset': question_formset,
        'classes': classes,
    })


def upload_test(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        logger.info("received excel file")
        try:
            # Gọi hàm xử lý file Excel
            questions = process_excel(file)
            logger.info("processing excel file")
            return JsonResponse({'success': True, 'questions': questions, 'total_questions': len(questions)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


def edit_test(request, test_id):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    test = Test.objects.filter(id=test_id).values_list('title', 'description', 'amount_of_time',
                                                       'attempt_limit').first()

    if not test:
        return HttpResponse("Test not found", status=404)

    title, description, amount_of_time, attempt_limit = test
    test_form = TestForm(initial={'title': title, 'description': description, 'amount_of_time': amount_of_time,
                                  'attempt_limit': attempt_limit})

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
                test.attempt_limit = test_form.cleaned_data['attempt_limit']
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
        'role_id': request.session.get('role_id'),
        'test_form': test_form,
        'test_id': test_id,
        'question_data': question_data,  # Truyền danh sách câu hỏi và lựa chọn
        'question_count': len(question_data),  # Số lượng câu hỏi hiện tại
        'classes': classes,
    })


def test_detail(request, test_id):
    # Lấy thông tin lịch sử làm bài kiểm tra
    history = StudentTest.objects.filter(test_id=test_id, student_id=request.session.get('user_id')).values()

    # Lấy thông tin bài thi
    test = Test.objects.get(id=test_id)

    attempt_limit = test.attempt_limit

    if attempt_limit is not None:
        attempted = attempt_limit - len(history)
        if attempted <= 0:
            can_test = False
        else:
            can_test = True
    else:
        attempted = "Không giới hạn"
        can_test = True

    request.session['test_id'] = test_id

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    user = User.objects.get(id=request.session.get('user_id'))

    profile_picture = user.profile_picture.url if user.profile_picture else None

    test_duration = test.amount_of_time

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
        "SELECT * FROM student_tests WHERE student_id = ? AND test_id = ? ORDER BY start_time DESC",
        (request.session['user_id'], test_id))
    history_student_test = cursor.fetchall()
    history_student_test = [list(i) for i in history_student_test]
    for i in history_student_test:
        i[3] = datetime.strptime(i[3], "%Y-%m-%d %H:%M:%S.%f")
        i[3] = i[3] + timedelta(hours=7)
        i[3] = i[3].strftime("%Y/%m/%d %H:%M")

        if i[4] is not None:
            i[4] = datetime.strptime(i[4], "%Y-%m-%d %H:%M:%S.%f")
            i[4] = i[4] + timedelta(hours=7)
            i[4] = i[4].strftime("%Y/%m/%d %H:%M")
        else:
            i[4] = 'Chưa nộp bài'
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

        else:
            # Người dùng nộp bài thi
            del request.session['test_id']
            total_question = len(questions_data)
            score = 0

            if action == 'submit_test':
                for question in questions_data:
                    question_id = str(question['id'])
                    correct_answer = next((choice[0] for choice in question['choices'] if choice[3]), None)
                    user_answer = request.POST.get(question_id)

                    if user_answer and int(user_answer) == correct_answer:
                        score += 1
            elif action == 'report_cheating':
                score = 0

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

            test_name = test.title

            student_test.append(score)
            student_test.append(total_question - score)
            student_test.append(total_question)
            student_test.append(test_name)
            student_test.append(test_id)

            conn.commit()
            conn.close()

            return render(request, 'test/result.html', {'student_test': student_test, 'total_question': total_question})

    conn.close()
    return render(request, 'test/test_detail.html', {
        'role_id': request.session.get('role_id'),
        'can_test': can_test,
        'name': name,
        'test': test,
        'attempted': attempted,
        'questions_data': questions_data,
        'history_student_test': history_student_test,
        'profile_picture': profile_picture
    })


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
    # Kiểm tra quyền của người dùng
    role_id = request.session.get('role_id')
    user_id = request.session.get('user_id')

    # Lọc danh sách lớp theo vai trò
    if role_id == 2:  # Giáo viên
        classes = ClassUser.objects.select_related('class_id__school_year').filter(
            user=user_id
        ).values_list(
            'class_id__id', 'class_id__name', 'class_id__school_year__name'
        ).order_by(
            'class_id__school_year__name', 'class_id__name'
        )
    elif role_id == 3:  # Quản trị viên
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute(
            "select c.id, c.name, sy.name,u.id, u.last_name, u.first_name from class c left join school_year sy on c.school_year_id = sy.id left join class_users cu on c.id = cu.class_id left join users u on cu.user_id = u.id where u.role_id = 2; ")
        classes = cursor.fetchall()
        conn.close()
    else:  # Không có quyền truy cập
        classes = []
        return render(request, 'class/class_list.html', {
            'role_id': role_id,
            'classes': classes,
        })

    # Tìm kiếm
    search_query = request.GET.get('search', '')
    if search_query:
        classes = classes.filter(
            Q(name__icontains=search_query) |
            Q(school_year__name__icontains=search_query)
        )

    # Chuyển đổi danh sách lớp sang dạng list để xử lý
    classes = list(classes)

    # Phân trang
    items_per_page = 10
    page_number = request.GET.get('page', 1)
    paginator = Paginator(classes, items_per_page)

    try:
        # Lấy trang hiện tại
        page_obj = paginator.get_page(page_number)
    except EmptyPage:
        # Nếu trang vượt quá giới hạn, trả về trang cuối cùng
        page_obj = paginator.get_page(paginator.num_pages)

    # Trả về dữ liệu cho template
    return render(request, 'class/class_list.html', {
        'role_id': role_id,
        'classes': page_obj.object_list,  # Danh sách lớp trên trang hiện tại
        'page_obj': page_obj,  # Đối tượng phân trang
        'search_query': search_query,  # Từ khóa tìm kiếm
    })


def create_class(request):
    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        school_year = request.POST.get('school_year')
        teacher_id = request.POST.get('teacher')
        descrip = request.POST.get('description') or ''

        # Kiểm tra đầu vào
        if not class_name or not school_year or not teacher_id:
            return JsonResponse({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin.'}, status=400)

        try:
            # Kiểm tra xem giáo viên có tồn tại không
            teacher = User.objects.get(id=teacher_id, role_id=2)  # role_id=2 là giáo viên
            student_ids = request.POST.getlist('student_ids[]')  # Lấy danh sách ID học sinh
            school_year = SchoolYear.objects.get(id=school_year)
            # Tạo lớp học mới
            class_obj = Class.objects.create(name=class_name, school_year=school_year, description=descrip)
            class_id = class_obj.id

            # Thêm giáo viên vào lớp
            ClassUser.objects.create(user=teacher, class_id=class_obj)
            # Thêm học sinh vào lớp
            for student_id in student_ids:
                student = User.objects.get(id=student_id)  # role_id=1 là học sinh
                ClassUser.objects.create(user=student, class_id=class_obj)
            return redirect('class_detail', class_id=class_obj.id)

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Không tìm thấy giáo viên với ID đã chọn.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

    # Lấy danh sách năm học và giáo viên
    school_years = SchoolYear.objects.all()
    teachers = User.objects.filter(role_id=2)

    return render(request, 'class/create_class.html', {
        'role_id': request.session.get('role_id'),
        'school_years': school_years,
        'teachers': teachers,
    })


@csrf_exempt
def upload_student_file(request):
    if request.method == "POST":
        file = request.FILES.get("excel-file")
        if not file:
            return JsonResponse({"error": "No file uploaded."}, status=400)

        try:
            # Đọc file Excel
            df = pd.read_excel(file)
            ids = df.iloc[:, 0].dropna().astype(int).tolist()

            students = []
            errors = []

            for student_id in ids:
                try:
                    student = User.objects.get(id=student_id)  # Lấy model tương ứng
                    students.append({
                        "id": student.id,
                        "username": student.username,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "email": student.email,
                        "phone": student.phone,
                        "gender": student.gender,
                        "date_of_birth": student.date_of_birth,
                    })
                except User.DoesNotExist:
                    errors.append(student_id)

            return JsonResponse({"students": students, "errors": errors})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request."}, status=400)


def delete_class(request, class_id):
    if request.method == 'POST':  # Chỉ chấp nhận phương thức POST
        try:
            class_data = Class.objects.get(id=class_id)
            class_data.delete()  # Xóa lớp khỏi cơ sở dữ liệu
            return JsonResponse({'success': True, 'message': 'Lớp đã được xóa thành công!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'})


def class_detail(request, class_id):
    # Lấy thông tin lớp học
    class_obj = get_object_or_404(Class.objects.prefetch_related('school_year'), id=class_id)
    class_info = {
        'id': class_obj.id,
        'name': class_obj.name,
        'school_year': class_obj.school_year.name if class_obj.school_year else '',
    }

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute(
        'select u.id, u.last_name, u.first_name from class_users cu left join users u on cu.user_id = u.id where cu.class_id = ? and u.role_id = 2',
        (class_id,))
    teacher = cursor.fetchone()
    # Tìm danh sách học sinh trong lớp
    cursor.execute(
        "select u.id, u.username ,u.first_name, u.last_name, u.email from class_users left join users u on class_users.user_id = u.id where u.role_id = 1 and class_id = ?",
        (class_id,))
    students = cursor.fetchall()
    # Xử lý danh sách học sinh
    students = [list(student) for student in students]
    for student in students:
        # Gộp họ và tên
        if student[2] is not None and student[3] is not None:
            student[2] = student[2] + ' ' + student[3]
        student.pop(3)  # Xóa cột họ hoặc tên đã gộp

    # Phân trang danh sách học sinh
    items_per_page = 10
    page_number = request.GET.get('page', 1)
    paginator = Paginator(students, items_per_page)

    try:
        page_obj = paginator.get_page(page_number)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Trả về template
    return render(request, 'class/class_detail.html', {
        'role_id': request.session.get('role_id'),  # ID của loại tài khoản
        'class_info': class_info,  # Thông tin lớp học
        'teacher': teacher,  # Thông tin giáo viên chủ nhiệm
        'students': page_obj.object_list,  # Danh sách học sinh trên trang hiện tại
        'page_obj': page_obj,  # Đối tượng phân trang
    })


def get_user_info(request, user_id):
    try:
        user_data = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'ID học sinh khong tồn tại'})

    user_info = {
        'id': user_data.id,
        'username': user_data.username,
        'email': user_data.email,
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'phone': user_data.phone,
        'date_of_birth': user_data.date_of_birth,
    }
    return JsonResponse({'success': True, 'user_info': user_info})


@csrf_exempt
def add_student_class(request, class_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('student_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Chưa nhập vào ID học sinh'})
        try:
            class_obj = Class.objects.get(id=class_id)
            user_obj = User.objects.get(id=user_id)

            if user_obj.role_id != 1:
                return JsonResponse({'success': False, 'message': 'Người dùng không phải là học sinh'})

            if ClassUser.objects.filter(class_id=class_obj, user=user_obj).exists():
                return JsonResponse({'success': False, 'message': 'Học sinh này đã tồn tại trong lớp'})

            class_user = ClassUser(class_id=class_obj, user=user_obj)
            class_user.save()
            return JsonResponse({'success': True, 'message': 'Học sinh đã được thêm vào lớp'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Gặp lỗi khi thêm học sinh vào lớp' + str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
def delete_student_class(request, class_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('student_id')
            class_user = ClassUser.objects.filter(class_id=class_id, user=user_id)
            class_user.delete()
            return JsonResponse({'success': True, 'message': 'Học sinh đã được xóa khỏi lớp'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Gặp lỗi khi xóa học sinh khỏi lớp' + str(e)})
