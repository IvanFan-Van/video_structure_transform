import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
from jose import jwt


def hash_password(password: str) -> str:
    """
    将明文密码加密为 bcrypt 哈希值
    """
    # 1. 将字符串转为字节流 (bcrypt 只接受 bytes)
    password_bytes = password.encode("utf-8")

    # 2. 生成盐值并进行哈希 (rounds 默认为 12，数值越大越慢越安全)
    # gensalt() 会自动处理盐值的生成
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))

    # 3. 将字节流解码为字符串，方便存入数据库
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证明文密码与数据库中的哈希值是否匹配
    """
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    # bcrypt.checkpw 会自动从 hashed_bytes 中提取盐值并进行比对
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """生成 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    # 注入过期时间
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, os.environ["SECRET_KEY"], algorithm=os.getenv("ALGORITHM", "HS256")
    )
    return encoded_jwt


def extract_json(text: str) -> dict | None:
    try:
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            text = match.group(1)

        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON 解码错误: {e}")
        return None


def timer(func):
    @wraps(func)  # 保留原函数的元数据（如函数名、文档字符串）
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # 使用高精度计时器
        result = func(*args, **kwargs)  # 执行原函数
        end_time = time.perf_counter()

        execution_time = end_time - start_time
        print(f"函数 [{func.__name__}] 运行耗时: {execution_time:.6f} 秒")
        return result  # 返回原函数的执行结果

    return wrapper


# --- 实战测试 ---
if __name__ == "__main__":
    raw_pwd = "my_super_secret_password_123"

    # 注册/存入数据库时：
    db_hash = hash_password(raw_pwd)
    print(f"存入数据库的哈希字符串:\n{db_hash}\n")
    # 输出类似于: $2b$12$L7pYhR... (包含了算法版本、计算强度和盐值)

    # 登录验证时：
    is_match = verify_password("my_super_secret_password_123", db_hash)
    is_wrong = verify_password("wrong_password", db_hash)

    print(f"正确密码验证结果: {is_match}")  # True
    print(f"错误密码验证结果: {is_wrong}")  # False
