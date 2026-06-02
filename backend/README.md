## Project Structure

- storage: 对象存储
- storage/videos: 存储用户上传的视频素材
- storage/images: 存储用户上传的图像素材
- src: 源码目录
- src/main.py: 入口文件
- src/models.py: 定义数据库模型, 例如 User, Asset 等
- src/utils.py: 定义一些辅助函数, 例如 `verify_password`, `hash_password`
- src/video.py: 定义 `VideoClip` 类, 用于保存 Video 信息
- tests/videos: 存放测试用的视频素材


## Quickstart

```bash
uv run src/main.py
```

## register and login logic
我们采用 OAuth + 邮箱密码登录两种方式

![alt text](./docs/assets/oauth.png)

### 数据库设计

`user` 表: 存储用户基础账号信息，支持邮箱密码登录。

字段：

- `id`: 主键
- `user_id`: 对外使用的用户标识
- `email`: 用户邮箱
- `password_hash`: 密码哈希，仅邮箱密码登录时使用
- `created_at`: 创建时间


`user_oauth` 表: 存储第三方 OAuth 绑定信息，一个用户可以绑定多个 OAuth 账号。

字段：

- `id`: 主键
- `user_id`: 外键，关联 `user.user_id`
- `provider`: 第三方平台名称，例如 `google`
- `provider_id`: 第三方平台返回的唯一用户标识

关系：

- `user` 与 `user_oauth` 为一对多关系
- OAuth 登录时先根据 `provider + provider_id` 查找绑定账号，未绑定时再创建或关联 `user`

## Schema 规范

该应用参考了 JSend 规范 [JSend 规范](./docs/JSend.md), 并重新设计了一个非常类似的 JSON specification

### 成功响应
```json
{
    "status": "success",
    "data": {
        "token": "xxx",
        "path": "xxx",
        "number": 123,
        ...
    }
}
```

### 失败响应
```json
{
    "status": "fail",
    "message": "xxx"
}
```

### 错误响应 
```json
{
    "status": "error",
    "message": "xxx"
}
```