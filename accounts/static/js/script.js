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
