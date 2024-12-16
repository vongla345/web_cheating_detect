import cv2
import requests
import time
# API endpoint
API_URL = "http://127.0.0.1:8081/"
def compare_image(reference_image, webcam_image):
    """
    Gửi yêu cầu so sánh ảnh tới API /authenticate.
    """
    try:
        files = {
            "reference_image": ("reference_image.jpg", open(reference_image, "rb"), "image/jpeg"),
            "webcam_image": ("webcam_image.jpg", open(webcam_image, "rb"), "image/jpeg"),
        }
        response = requests.post(API_URL + 'authenticate', files=files)
        if response.status_code == 200:
            result = response.json()
            print(f"Similarity: {result['data']['similarity']:.2f}%, Status: {result['data']['status']}")
        else:
            print(f"Lỗi API: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Lỗi khi gửi yêu cầu: {e}")
def authenticate_via_webcam(reference_image):
    """
    Mở webcam và chụp ảnh liên tục, gửi ảnh tới API để xác thực.
    """
    cap = cv2.VideoCapture(0)  # Mở webcam
    if not cap.isOpened():
        print("Không thể mở webcam. Vui lòng kiểm tra kết nối.")
        return
    print("Đang bật webcam. Nhấn ESC để thoát.")
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc dữ liệu từ webcam.")
            break
        # Hiển thị khung hình
        cv2.imshow("Webcam", frame)
        # Chụp và lưu ảnh mỗi 5 giây (dựa vào frame_count)
        if frame_count % 150 == 0:  # Webcam mặc định chạy ở 30 FPS
            webcam_image_path = "./webcam_image.jpg"
            cv2.imwrite(webcam_image_path, frame)
            print("Đã chụp ảnh từ webcam. Đang gửi tới API...")
            # Gửi yêu cầu so sánh với ảnh tham chiếu
            compare_image(reference_image, webcam_image_path)
        frame_count += 1
        # Kiểm tra phím ESC để thoát
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            print("Thoát chương trình.")
            break
    # Giải phóng webcam và đóng cửa sổ hiển thị
    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    # Đường dẫn ảnh tham chiếu
    REFERENCE_IMAGE = "Nhan.jpg"  # Đảm bảo ảnh tham chiếu tồn tại
    # Bắt đầu xác thực qua webcam
    authenticate_via_webcam(REFERENCE_IMAGE)