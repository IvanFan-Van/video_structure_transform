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

    asset_id = str(uuid.uuid4())
    filename = f"{asset_id}{ext}"
    filepath = VIDEO_STORAGE_DIR / filename

    content = await file.read()
    filepath.write_bytes(content)

    try:
        meta = probe_video(filepath)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        return {
            "success": False,
            "status": 500,
            "message": "Failed to probe video metadata.",
            "error": {
                "code": "PROBE_FAILED",
                "details": str(e),
            },
        }, 500

    with Session(engine) as session:
        asset = Asset(
            asset_id=asset_id,
            user_id=current_user.user_id,
            path=str(filepath),
            type="video",
        )
        session.add(asset)
        session.commit()

    return {
        "success": True,
        "status": 201,
        "message": "Video uploaded successfully.",
        "data": {
            "asset_id": asset_id,
            "type": "video",
            "path": str(filepath),
            "metadata": meta.to_dict(),
        },
    }


@app.post("/compress")
async def compress_video_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    data = await request.json()
    asset_id = data.get("asset_id")

    if not asset_id:
        return {
            "success": False,
            "status": 400,
            "message": "asset_id is required.",
            "error": {
                "code": "MISSING_ASSET_ID",
                "details": "The asset_id of the source video must be provided.",
            },
        }, 400

    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        source_asset = session.exec(statement).first()

        if not source_asset:
            return {
                "success": False,
                "status": 404,
                "message": f"Asset with id '{asset_id}' not found.",
                "error": {
                    "code": "ASSET_NOT_FOUND",
                    "details": f"No asset found with asset_id '{asset_id}'.",
                },
            }, 404

        source_path = Path(source_asset.path)
        if not source_path.exists():
            return {
                "success": False,
                "status": 500,
                "message": "Source file not found on disk.",
                "error": {
                    "code": "FILE_MISSING",
                    "details": f"Asset record exists but file is missing at '{source_asset.path}'.",
                },
            }, 500

        compressed_asset_id = str(uuid.uuid4())
        compressed_filename = f"{compressed_asset_id}_compressed.mp4"
        compressed_path = VIDEO_STORAGE_DIR / compressed_filename
        VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        vcodec = data.get("vcodec", "libx264")
        crf = data.get("crf", 32)
        target_v_bitrate = data.get("target_v_bitrate")
        scale_width = data.get("scale_width")
        max_fps = data.get("max_fps", 30)
        acodec = data.get("acodec", "aac")
        target_a_bitrate = data.get("target_a_bitrate", "96k")

        try:
            compress_video(
                source_path,
                compressed_path,
                vcodec=vcodec,
                crf=crf,
                target_v_bitrate=target_v_bitrate,
                scale_width=scale_width,
                max_fps=max_fps,
                acodec=acodec,
                target_a_bitrate=target_a_bitrate,
            )
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
        except Exception as e:
            compressed_path.unlink(missing_ok=True)
            return {
                "success": False,
                "status": 500,
                "message": "Failed to probe compressed video metadata.",
                "error": {
                    "code": "PROBE_FAILED",
                    "details": str(e),
                },
            }, 500

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
        "message": "Video compressed successfully.",
        "data": {
            "asset_id": compressed_asset_id,
            "source_asset_id": asset_id,
            "type": "video",
            "path": str(compressed_path),
            "metadata": compressed_meta.to_dict(),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
