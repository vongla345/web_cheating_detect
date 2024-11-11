import cv2
import logging

# Cấu hình logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_camera():
    cap = cv2.VideoCapture(0)  # Mở camera mặc định

    if not cap.isOpened():
        logger.error("Không thể mở camera.")
        return

    logger.info("Camera mở thành công. Nhấn 'Q' để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Không thể đọc khung hình từ camera.")
            break

        # Hiển thị khung hình
        cv2.imshow("Camera Test", frame)

        # Thoát nếu nhấn 'Q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Đã giải phóng tài nguyên camera.")


# Chạy thử camera
test_camera()
