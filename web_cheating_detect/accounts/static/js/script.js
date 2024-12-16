function switchAccountType(type) {
    // Thay đổi giá trị của trường hidden 'role'
    document.getElementById('account-type').value = type;

    // Lấy các tab của học sinh và giáo viên
    const studentTab = document.getElementById('student-tab');
    const teacherTab = document.getElementById('teacher-tab');

    // Chuyển đổi giữa các tab khi người dùng chọn
    if (type === 'student') {
        studentTab.classList.add('active');
        teacherTab.classList.remove('active');
    } else {
        teacherTab.classList.add('active');
        studentTab.classList.remove('active');
    }
}

let currentQuestionIndex = 0; // Chỉ số câu hỏi hiện tại
const questions = document.querySelectorAll('.question'); // Lấy tất cả các câu hỏi
const questionButtons = document.querySelectorAll('.question-btn'); // Lấy tất cả các nút câu hỏi

// Hiển thị câu hỏi đầu tiên
showQuestion(questions[0].id.split('-')[1]);

function showQuestion(questionId) {
    questions.forEach(question => (question.style.display = 'none'));

    // Hiển thị câu hỏi được chọn
    document.getElementById(`question-${questionId}`).style.display = 'block';

    // Cập nhật chỉ số hiện tại
    currentQuestionIndex = Array.from(questions).findIndex(q => q.id === `question-${questionId}`);

    // Hiển thị/Ẩn nút "Câu trước" và "Câu sau"
    document.getElementById('prev-btn').style.visibility =
        currentQuestionIndex === 0 ? 'hidden' : 'visible';
    document.getElementById('next-btn').style.visibility =
        currentQuestionIndex === questions.length - 1 ? 'hidden' : 'visible';
}

function updateQuestionStatus(questionId) {
    // Đánh dấu câu hỏi đã được trả lời
    const btn = document.getElementById(`question-btn-${questionId}`);
    btn.classList.add('completed');
}

function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        showQuestion(questions[currentQuestionIndex + 1].id.split('-')[1]);
    }
}

function prevQuestion() {
    if (currentQuestionIndex > 0) {
        showQuestion(questions[currentQuestionIndex - 1].id.split('-')[1]);
    }
}

function checkCompletion() {
    // Kiểm tra xem tất cả các câu hỏi đã được trả lời chưa
    let allAnswered = true;

    // Lặp qua tất cả các câu hỏi
    questions.forEach((question, index) => {
        const inputs = question.querySelectorAll('input[type="radio"]');
        const answered = Array.from(inputs).some(input => input.checked);

        if (!answered) {
            allAnswered = false;
        }
    });

    if (!allAnswered) {
        alert('Bạn chưa trả lời đủ tất cả các câu hỏi!');
        return false;
    }

    return allAnswered;
}

