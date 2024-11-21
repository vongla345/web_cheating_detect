from django import forms
from django.forms import formset_factory
import sqlite3


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập username'}),
        error_messages={'required': 'Vui lòng nhập username.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mật khẩu'}),
        required=True,
        error_messages={'required': 'Vui lòng nhập mật khẩu.'}
    )

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'Nhập tên đăng nhập'}))
    first_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Họ'}))
    last_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Tên'}))
    email = forms.EmailField(max_length=255, required=True, widget=forms.EmailInput(attrs={'placeholder': 'Nhập email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Nhập mật khẩu'}), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Nhập lại mật khẩu'}), required=True)
    role = forms.CharField(widget=forms.HiddenInput(), initial='student')
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Mật khẩu không trùng khớp")
        return cleaned_data

    def save(self):
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()

        username = self.cleaned_data['username']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        role = self.cleaned_data['role']

        if role == 'teacher':
            role = 2
        else:
            role = 1

        # Thêm user vào database
        cursor.execute("INSERT INTO users (username, first_name, last_name, email, password, role_id) VALUES (?, ?, ?, ?, ?,?)",
                       (username, first_name, last_name, email, password, role))
        conn.commit()
        conn.close()

class ChoiceForm(forms.Form):
    choice_text = forms.CharField(max_length=255, required=True, label="Choice")
    is_correct = forms.BooleanField(required=False, label="Correct Answer")

class QuestionForm(forms.Form):
    question_text = forms.CharField(max_length=255, required=True, label="Question")

ChoiceFormSet = formset_factory(ChoiceForm, min_num=4, max_num=4, extra=0)
QuestionFormSet = formset_factory(QuestionForm, min_num=0, extra=0)

class TestForm(forms.Form):
    title = forms.CharField(max_length=255, required=True, label="Test Title")
    description = forms.CharField(max_length=255, required=False, label="Description")