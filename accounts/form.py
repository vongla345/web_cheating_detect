from django import forms
from django.forms import formset_factory
import sqlite3


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=254, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self):
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()

        username = self.cleaned_data['username']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']

        # Thêm user vào database
        cursor.execute("INSERT INTO users (username, first_name, last_name, email, password) VALUES (?, ?, ?, ?, ?)",
                       (username, first_name, last_name, email, password))
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