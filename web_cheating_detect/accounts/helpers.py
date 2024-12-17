import pandas as pd

def process_excel(file):
    """
    Hàm xử lý file Excel chứa câu hỏi và đáp án.
    Đầu vào: file Excel (dạng file-like object).
    Đầu ra: Danh sách câu hỏi với các lựa chọn và trạng thái đúng/sai.
    """
    # Đọc file Excel
    df = pd.read_excel(file)

    questions = []
    current_question = None
    for _, row in df.iterrows():
        if not pd.isna(row['Câu hỏi']):
            # Gặp dòng mới -> thêm câu hỏi
            current_question = {
                'question_text': row['Câu hỏi'],
                'choices': []
            }
            questions.append(current_question)
        # Thêm choice vào câu hỏi hiện tại
        if current_question:
            is_correct = str(row['Đúng']).strip().upper() == '1.0'
            current_question['choices'].append({
                'choice_text': row['Đáp án'],
                'is_correct': is_correct
            })
    return questions

