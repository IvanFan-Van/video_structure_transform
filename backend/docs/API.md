# API 接口文档

Base URL: `http://127.0.0.1:8000`

---

## 目录

- [通用说明](#通用说明)
- [1. GET / — 健康检查](#1-get----健康检查)
- [2. POST /register — 用户注册](#2-post-register--用户注册)
- [3. POST /login — 用户登录](#3-post-login--用户登录)
- [4. GET /protected — 受保护路由](#4-get-protected--受保护路由)
- [5. POST /upload — 上传视频](#5-post-upload--上传视频)
- [6. POST /compress — 压缩视频](#6-post-compress--压缩视频)
- [附录 A: VideoMeta 元数据字段](#附录-a-videometa-元数据字段)
- [附录 B: 错误码参考](#附录-b-错误码参考)
- [附录 C: 支持的视频格式](#附录-c-支持的视频格式)

---

## 通用说明

### 响应格式

所有接口统一返回 JSON，结构如下：

**成功响应：**

```json
{
  "success": true,
  "status": 200,
  "message": "操作描述",
  "data": { ... }
}
```

**失败响应：**

```json
{
  "success": false,
  "status": 400,
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": "详细错误信息"
  }
}
```

### 认证

需要认证的接口使用 **Bearer Token** 方式，请求头中携带：

```
Authorization: Bearer <access_token>
```

Token 通过 `/login` 接口获取。

---

## 1. GET / — 健康检查

检查服务是否正常运行。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 不需要 |

### 请求参数

无

### 响应示例

```json
{
  "status": "ok"
}
```

---

## 2. POST /register — 用户注册

注册新用户账号。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 不需要 |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `email` | string | 是 | 用户邮箱 |
| `password` | string | 是 | 用户密码（明文，服务端 bcrypt 加密） |

### 请求示例

```json
{
  "email": "user@example.com",
  "password": "my_secure_password"
}
```

### 成功响应 (201)

```json
{
  "success": true,
  "status": 201,
  "message": "User registered successfully.",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

### 错误码

| code | 说明 |
|---|---|
| `MISSING_FIELDS` | email 或 password 未提供 |
| `USER_ALREADY_EXISTS` | 该邮箱已被注册 |

---

## 3. POST /login — 用户登录

使用邮箱和密码登录，获取 JWT 访问令牌。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 不需要 |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `email` | string | 是 | 注册邮箱 |
| `password` | string | 是 | 密码 |

### 请求示例

```json
{
  "email": "user@example.com",
  "password": "my_secure_password"
}
```

### 成功响应 (200)

```json
{
  "success": true,
  "status": 200,
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com"
    }
  }
}
```

### 错误码

| code | 说明 |
|---|---|
| `MISSING_CREDENTIALS` | email 或 password 未提供 |
| `USER_NOT_FOUND` | 该邮箱未注册 |
| `PASSWORD_NOT_SET` | 该用户通过 Google OAuth 注册，未设置本地密码 |
| `INVALID_PASSWORD` | 密码不正确 |

---

## 4. GET /protected — 受保护路由

测试认证是否生效的调试接口。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 需要（Bearer Token） |

### 请求头

```
Authorization: Bearer <access_token>
```

### 成功响应 (200)

```json
{
  "status": "ok"
}
```

### 认证失败 (401)

```json
{
  "detail": "凭证已过期或无效，请重新登录"
}
```

---

## 5. POST /upload — 上传视频

将视频文件上传到服务器，保存到本地并记录到数据库。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `multipart/form-data` |

### 请求头

```
Authorization: Bearer <access_token>
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | 是 | 视频文件（支持格式见附录 C） |

### 请求示例 (curl)

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/video.mp4"
```

### 成功响应 (201)

```json
{
  "success": true,
  "status": 201,
  "message": "Video uploaded successfully.",
  "data": {
    "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "type": "video",
    "path": "storage\\videos\\a1b2c3d4-e5f6-7890-abcd-ef1234567890.mp4",
    "metadata": {
      "filepath": "D:\\HKU\\...\\storage\\videos\\a1b2c3d4....mp4",
      "codec": "h264",
      "width": 1920,
      "height": 1080,
      "fps": 30.0,
      "v_bitrate": 2500,
      "total_bitrate": 2700,
      "audio_sample_rate": 44100,
      "audio_channels": 2,
      "a_bitrate": 128,
      "size": 10485760,
      "duration": 15.5
    }
  }
}
```

### 错误码

| code | 说明 |
|---|---|
| `INVALID_FILE_TYPE` | 文件类型不支持（不是视频格式） |
| `PROBE_FAILED` | 视频元数据提取失败 |

---

## 6. POST /compress — 压缩视频

对已上传的视频执行压缩，所有压缩参数均为可选。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `asset_id` | string | **是** | — | 源视频的 asset_id（由 /upload 返回） |
| `vcodec` | string | 否 | `"libx264"` | 视频编码器：`libx264` / `libx265` |
| `crf` | int \| null | 否 | `32` | 恒定质量因子（0-51，值越小质量越高体积越大）。设为 `null` 且设置 `target_v_bitrate` 时使用固定码率模式 |
| `target_v_bitrate` | string \| null | 否 | `null` | 目标视频码率，如 `"2M"`、`"1500k"`。设置后忽略 `crf`，使用固定码率编码 |
| `scale_width` | int \| null | 否 | `null` | 缩放目标宽度（像素），高度等比缩放。如 `720` 缩放到 720p |
| `max_fps` | int \| null | 否 | `30` | 最大帧率限制，设为 `null` 保持原始帧率 |
| `acodec` | string | 否 | `"aac"` | 音频编码器：`aac` / `libmp3lame` |
| `target_a_bitrate` | string | 否 | `"96k"` | 目标音频码率，如 `"128k"`、`"64k"` |

### 请求示例

**最简请求（全部使用默认值）：**

```json
{
  "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**自定义压缩参数：**

```json
{
  "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "vcodec": "libx264",
  "crf": 28,
  "scale_width": 720,
  "max_fps": 24,
  "target_a_bitrate": "128k"
}
```

**使用固定码率模式：**

```json
{
  "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "target_v_bitrate": "2M",
  "max_fps": 30,
  "acodec": "aac",
  "target_a_bitrate": "96k"
}
```

### 成功响应 (201)

```json
{
  "success": true,
  "status": 201,
  "message": "Video compressed successfully.",
  "data": {
    "asset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "source_asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "type": "video",
    "path": "storage\\videos\\b2c3d4e5-f6a7-8901-bcde-f12345678901_compressed.mp4",
    "metadata": {
      "filepath": "D:\\HKU\\...\\storage\\videos\\b2c3d4e5....mp4",
      "codec": "h264",
      "width": 720,
      "height": 404,
      "fps": 24.0,
      "v_bitrate": 800,
      "total_bitrate": 900,
      "audio_sample_rate": 44100,
      "audio_channels": 2,
      "a_bitrate": 128,
      "size": 3145728,
      "duration": 15.5
    }
  }
}
```

### 错误码

| code | 说明 |
|---|---|
| `MISSING_ASSET_ID` | 未提供 asset_id |
| `ASSET_NOT_FOUND` | 该 asset_id 对应的记录不存在 |
| `FILE_MISSING` | 数据库中记录存在但磁盘文件已丢失 |
| `COMPRESS_FAILED` | 视频压缩过程失败（如编码器不支持、参数异常） |
| `PROBE_FAILED` | 压缩后视频的元数据提取失败 |

---

## 附录 A: VideoMeta 元数据字段

上传和压缩接口返回的 `metadata` 对象包含以下字段：

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `filepath` | string | 文件绝对路径 | `"D:\\...\\storage\\videos\\abc.mp4"` |
| `codec` | string \| null | 视频编码格式 | `"h264"` / `"hevc"` |
| `width` | int \| null | 视频宽度（像素） | `1920` |
| `height` | int \| null | 视频高度（像素） | `1080` |
| `fps` | float \| null | 帧率 | `30.0` / `23.976` |
| `v_bitrate` | int \| null | 视频码率（kbps） | `2500` |
| `total_bitrate` | int \| null | 总码率（kbps） | `2700` |
| `audio_sample_rate` | int \| null | 音频采样率（Hz） | `44100` / `48000` |
| `audio_channels` | int \| null | 音频声道数 | `1` / `2` |
| `a_bitrate` | int \| null | 音频码率（kbps） | `128` |
| `size` | int \| null | 文件大小（字节） | `10485760` |
| `duration` | float \| null | 视频时长（秒） | `15.5` |

## 附录 B: 错误码参考

| 错误码 | HTTP 状态码 | 说明 |
|---|---|---|
| `MISSING_FIELDS` | 400 | 必填字段缺失 |
| `MISSING_CREDENTIALS` | 400 | 登录凭据缺失 |
| `MISSING_ASSET_ID` | 400 | 压缩请求缺少 asset_id |
| `USER_ALREADY_EXISTS` | 400 | 注册邮箱已存在 |
| `USER_NOT_FOUND` | 404 | 登录邮箱未注册 |
| `INVALID_PASSWORD` | 401 | 密码不正确 |
| `INVALID_FILE_TYPE` | 400 | 上传文件类型不支持 |
| `PASSWORD_NOT_SET` | 500 | 用户通过 OAuth 注册，无本地密码 |
| `ASSET_NOT_FOUND` | 404 | Asset 记录不存在 |
| `FILE_MISSING` | 500 | Asset 记录存在但磁盘文件丢失 |
| `PROBE_FAILED` | 500 | 视频元数据探测失败 |
| `COMPRESS_FAILED` | 500 | 视频压缩失败 |

## 附录 C: 支持的视频格式

| 扩展名 | MIME 类型 | 说明 |
|---|---|---|
| `.mp4` | `video/mp4` | MPEG-4 视频 |
| `.mov` | `video/quicktime` | QuickTime 视频 |
| `.avi` | `video/x-msvideo` | AVI 视频 |
| `.mkv` | `video/x-matroska` | Matroska 视频 |
| `.webm` | `video/webm` | WebM 视频 |
| `.flv` | `video/x-flv` | Flash 视频 |
| `.wmv` | `video/x-ms-wmv` | Windows Media 视频 |
