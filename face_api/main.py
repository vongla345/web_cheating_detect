from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import face_recognition
from io import BytesIO
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from typing import Optional

app = FastAPI(redirect_slashes=False)

origins = [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",  # Thêm địa chỉ này nếu frontend chạy tại đây
    "http://127.0.0.1:8080",
    "http://104.214.177.160",
    "https://104.214.177.160",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DataModel(BaseModel):
    similarity: float
    status: str


class SimilarityResponse(BaseModel):
    success: bool
    data: Optional[DataModel] = None
    error: Optional[dict] = None
    message: str


def get_face_encoding(image_file: UploadFile, image_type: str):
    try:
        # Kiểm tra định dạng file
        print(f"Uploaded file type: {image_file.content_type}")
        print(f"Uploaded file name: {image_file.filename}")
        if image_file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type for the {image_type} image. Only JPEG and PNG are supported."
            )

        # Đọc file và chuyển thành image
        image = Image.open(BytesIO(image_file.file.read()))
        print(f"Processing {image_type} image: Image mode is {image.mode}")

        # Chuyển đổi về RGB nếu cần
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = np.array(image)

        # Trích xuất face encoding
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No face detected in the {image_type} image."
            )

        if len(face_encodings) > 1:
            raise HTTPException(
                status_code=400,
                detail=f"More than one face detected in the {image_type} image."
            )

        return face_encodings[0]

    except HTTPException as http_exc:
        print(f"Error during {image_type} image processing: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        print(f"Unexpected error processing the {image_type} image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing the {image_type} image: {str(e)}"
        )


@app.post("/authenticate", response_model=SimilarityResponse)
async def compare_faces(
        reference_image: UploadFile = File(...),
        webcam_image: UploadFile = File(...)
):
    try:
        # Trích xuất face encoding từ ảnh tham chiếu
        print("Processing reference image...")
        reference_encoding = get_face_encoding(reference_image, "reference")

        # Trích xuất face encoding từ ảnh webcam
        print("Processing webcam image...")
        webcam_encoding = get_face_encoding(webcam_image, "webcam")

        # Tính toán khoảng cách khuôn mặt
        face_distance = face_recognition.face_distance([reference_encoding], webcam_encoding)[0]
        print(f"Face distance: {face_distance}")

        # Tính toán độ tương đồng
        similarity = (1 - face_distance) * 100
        print(f"Similarity: {similarity}%")

        # Xác định trạng thái xác thực
        status = "approved" if similarity >= 50 else "not approved"
        print(f"Authentication status: {status}")

        return SimilarityResponse(
            success=True,
            data=DataModel(similarity=similarity, status=status),
            message="Face verification successful."
        )

    except HTTPException as http_exc:
        return SimilarityResponse(
            success=False,
            error={
                "code": http_exc.status_code,
                "type": "FaceDetectionError",
                "detail": http_exc.detail
            },
            message="Error during face verification."
        )

    except Exception as e:
        return SimilarityResponse(
            success=False,
            error={
                "code": 500,
                "type": "UnexpectedError",
                "detail": str(e)
            },
            message="An unexpected error occurred during face verification."
        )


def validate_image_file(image_file: UploadFile):
    try:
        # Đọc file và kiểm tra định dạng
        img = Image.open(BytesIO(image_file.file.read()))
        img.verify()  # Kiểm tra nếu file không phải ảnh
        image_file.file.seek(0)  # Reset pointer để sử dụng tiếp
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Yêu cầu phải là định dạng ảnh."
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing image: {str(e)}"
        )
    return True


@app.post("/check-face/")
async def check_face(image: UploadFile = File(...)):
    """
    Check if an uploaded image contains a face.
    """
    try:
        # Validate file format
        validate_image_file(image)

        # Read the uploaded image
        img_bytes = await image.read()
        img = Image.open(BytesIO(img_bytes))
        img_array = face_recognition.load_image_file(BytesIO(img_bytes))

        # Detect faces
        face_locations = face_recognition.face_locations(img_array)

        if len(face_locations) == 0:
            return {"status": "error", "message": "Không tìm thấy khuôn mặt hợp lệ nào"}
        return {"status": "success", "message": "Phát hiện khuôn mặt hợp lệ."}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
