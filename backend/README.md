## Project Structure

- storage: 对象存储
- storage/videos: 存储用户上传的视频素材
- storage/audios: 存储从视频中分离出的背景音乐（BGM）
- storage/images: 存储用户上传的图像素材
- src: 源码目录
- src/main.py: 入口文件
- src/models.py: 定义数据库模型, 例如 User, Asset 等
- src/audio.py: 音频特征提取、BGM 分离、流式分析
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

## API 接口

完整的 API 接口文档见 [docs/API.md](./docs/API.md)。

### 新增：`GET /analyze-audio?asset_id=xxx`

传入已上传视频的 `asset_id`，自动分离背景音乐并逐帧流式返回音乐特征（SSE）。

- 首次请求会自动使用 `audio_separator` 分离人声/伴奏，仅保留伴奏（bgm.mp3）
- 分离结果缓存到数据库（`type="audio"`），后续请求直接使用缓存
- 每秒推送约 43 帧，每帧包含局部特征（rms, spectral_centroid 等）和渐进全局特征（BPM, 动态范围, genre, duration）
- 每帧的 `asset_id` 字段即为 BGM 音频的数据库 UUID，可用于后续请求

```bash
curl -N "http://127.0.0.1:8000/analyze-audio?asset_id=xxx" \
  -H "Authorization: Bearer <token>"
```

响应为 `text/event-stream` 格式，每行 `data: {json}` 为一帧数据。

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

## Quickstart

初始化环境
```
uv sync
```

启动后端
```
uv run uvicorn app.main:app
```
