import os
import uuid
from datetime import timedelta
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from models import Asset, User, engine
from utils import create_access_token, hash_password, verify_password
from video import VideoMeta, compress_video, probe_video

load_dotenv(find_dotenv())

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证已过期或无效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            os.environ["SECRET_KEY"],
            algorithms=[os.getenv("ALGORITHM", "HS256")],
        )
        user_id: str = payload.get("user_id", None)  # type: ignore
        if user_id is None:
            raise credentials_exception

        with Session(engine) as session:
            statement = select(User).where(User.user_id == user_id)
            user = session.exec(statement).first()
            if user is None:
                raise credentials_exception

            return user

    except JWTError:
        raise credentials_exception


@app.get("/")
def index():
    return {"status": "ok"}


@app.post("/register")
async def register(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "success": False,
            "status": 400,
            "message": "Email and password are required.",
            "error": {
                "code": "MISSING_FIELDS",
                "details": "Both email and password must be provided.",
            },
        }, 400

    with Session(engine) as session:
        # CHECK IF USER EXISTS
        statement = select(User).where(User.email == data["email"])
        result = session.exec(statement).first()
        if result:
            return {
                "success": False,
                "status": 400,
                "message": f"User with email {email} already exists.",
                "error": {
                    "code": "USER_ALREADY_EXISTS",
                    "details": f"Email {email} is already registered.",
                },
            }, 400

        # CREATE USER
        user = User(
            user_id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password(password),
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "success": True,
            "status": 201,
            "message": "User registered successfully.",
            "data": {
                "user_id": user.user_id,
                "email": user.email,
            },
        }


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email", None)
    password = data.get("password", None)
    if not email or not password:
        return {
            "success": False,
            "status": 400,
            "message": "Email and password are required.",
            "error": {
                "code": "MISSING_CREDENTIALS",
                "details": "Both email and password must be provided.",
            },
        }, 400

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        # CHECK IF USER EXISTS
        user = session.exec(statement).first()
        if not user:
            return {
                "success": False,
                "status": 404,
                "message": f"User with email {email} not found.",
                "error": {
                    "code": "USER_NOT_FOUND",
                    "details": f"No user registered with email {email}.",
                },
            }, 404

        # CHECK IF USER LOGINS WITH GOOGLE OAUTH
        if user.password_hash is None:
            return {
                "success": False,
                "status": 500,
                "message": "User does not have a local password set. This account is likely registered via Google OAuth. Please use 'Login with Google' or reset your password to set a local password.",
                "error": {
                    "code": "PASSWORD_NOT_SET",
                    "details": "User does not have a local password set. This account is likely registered via Google OAuth. Please use 'Login with Google' or reset your password to set a local password.",
                },
            }, 500

        # INCORRECT PASSWORD
        if not verify_password(password, user.password_hash):
            return {
                "success": False,
                "status": 401,
                "message": "Invalid password.",
                "error": {
                    "code": "INVALID_PASSWORD",
                    "details": "The provided password is incorrect.",
                },
            }, 401

        token = create_access_token(
            data={"user_id": user.user_id, "email": user.email},
            expires_delta=timedelta(
                minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
            ),
        )

        return {
            "success": True,
            "status": 200,
            "message": "Login successful.",
            "data": {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                },
            },
        }


@app.get("/protected")
async def test(request: Request, current_user: User = Depends(get_current_user)):
    print(current_user)
    return {"status": "ok"}


STORAGE_DIR = Path("storage")
VIDEO_STORAGE_DIR = STORAGE_DIR / "videos"
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/x-ms-wmv",
}


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "upload.mp4").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS and file.content_type not in ALLOWED_VIDEO_MIME_TYPES:
        return {
            "success": False,
            "status": 400,
            "message": "Unsupported file type.",
            "error": {
                "code": "INVALID_FILE_TYPE",
                "details": f"File type '{file.content_type}' (ext '{ext}') is not a supported video format.",
            },
        }, 400

    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    original_asset_id = str(uuid.uuid4())
    compressed_asset_id = str(uuid.uuid4())
    video_id = original_asset_id

    original_filename = f"{original_asset_id}{ext}"
    compressed_filename = f"{compressed_asset_id}_compressed.mp4"
    original_path = VIDEO_STORAGE_DIR / original_filename
    compressed_path = VIDEO_STORAGE_DIR / compressed_filename

    content = await file.read()
    original_path.write_bytes(content)

    try:
        original_meta = probe_video(original_path)
    except Exception as e:
        original_path.unlink(missing_ok=True)
        return {
            "success": False,
            "status": 500,
            "message": "Failed to probe video metadata.",
            "error": {
                "code": "PROBE_FAILED",
                "details": str(e),
            },
        }, 500

    try:
        compress_video(original_path, compressed_path)
    except Exception as e:
        compressed_path.unlink(missing_ok=True)
        return {
            "success": False,
            "status": 500,
            "message": "Failed to compress video.",
            "error": {
                "code": "COMPRESS_FAILED",
                "details": str(e),
            },
        }, 500

    try:
        compressed_meta = probe_video(compressed_path)
    except Exception:
        compressed_meta = None

    with Session(engine) as session:
        original_asset = Asset(
            asset_id=original_asset_id,
            user_id=current_user.user_id,
            path=str(original_path),
            type="video",
        )
        session.add(original_asset)

        compressed_asset = Asset(
            asset_id=compressed_asset_id,
            user_id=current_user.user_id,
            path=str(compressed_path),
            type="video",
        )
        session.add(compressed_asset)

        session.commit()

    return {
        "success": True,
        "status": 201,
        "message": "Video uploaded and compressed successfully.",
        "data": {
            "video_id": video_id,
            "original": {
                "asset_id": original_asset_id,
                "path": str(original_path),
                **original_meta.to_dict(),
            },
            "compressed": {
                "asset_id": compressed_asset_id,
                "path": str(compressed_path),
                **(compressed_meta.to_dict() if compressed_meta else {}),
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
