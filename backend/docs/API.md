# API 接口文档

Base URL: `http://127.0.0.1:8000`

---

## 目录

- [API 接口文档](#api-接口文档)
  - [目录](#目录)
  - [通用说明](#通用说明)
    - [响应格式](#响应格式)
    - [认证](#认证)
  - [1. GET / — 健康检查](#1-get---健康检查)
    - [请求参数](#请求参数)
    - [响应示例](#响应示例)
  - [2. POST /register — 用户注册](#2-post-register--用户注册)
    - [请求参数](#请求参数-1)
    - [请求示例](#请求示例)
    - [成功响应 (201)](#成功响应-201)
    - [错误响应](#错误响应)
  - [3. POST /login — 用户登录](#3-post-login--用户登录)
    - [请求参数](#请求参数-2)
    - [请求示例](#请求示例-1)
    - [成功响应 (200)](#成功响应-200)
    - [错误响应](#错误响应-1)
  - [4. POST /upload — 上传视频](#4-post-upload--上传视频)
    - [请求参数](#请求参数-3)
    - [请求示例 (curl)](#请求示例-curl)
    - [成功响应 (201)](#成功响应-201-1)
    - [错误响应](#错误响应-2)
  - [5. POST /compress — 压缩视频](#5-post-compress--压缩视频)
    - [请求参数](#请求参数-4)
    - [请求示例](#请求示例-2)
    - [成功响应 (202)](#成功响应-202-2)
    - [错误响应](#错误响应-3)
  - [6. POST /analyze-script — 提取视频叙事结构](#6-post-analyze-script--提取视频叙事结构)
    - [请求参数](#请求参数-5)
    - [请求示例](#请求示例-3)
    - [成功响应 (202)](#成功响应-202-2)
    - [错误响应](#错误响应-4)
  - [7. GET /task/{task_id} — 查询异步任务状态](#7-get-tasktask_id--查询异步任务状态)
  - [8. POST /task/{task_id}/cancel — 取消异步任务](#8-post-tasktask_idcancel--取消异步任务)
  - [附录 A: VideoMeta 元数据字段](#附录-a-videometa-元数据字段)
  - [附录 B: 错误码参考](#附录-b-错误码参考)
  - [附录 C: 支持的视频格式](#附录-c-支持的视频格式)
  - [附录 D: 异步任务与取消](#附录-d-异步任务与取消)

---

## 通用说明

### 响应格式

所有接口统一返回 JSON，遵循 JSend 规范：

**成功响应：**

```json
{
  "status": "success",
  "data": { ... }
}
```

**客户端错误响应 (4xx)：**

```json
{
  "status": "fail",
  "message": "错误描述"
}
```

**服务端错误响应 (5xx)：**

```json
{
  "status": "error",
  "message": "错误描述"
}
```

部分 5xx 错误会附带额外的错误码和详情：

```json
{
  "status": "error",
  "message": "错误描述",
  "data": {
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

Token 通过 `/login` 接口获取，默认有效期为 15 分钟（可通过环境变量 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置）。

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
  "status": "success",
  "data": "ok"
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
| `password` | string | 是 | 用户密码（明文，服务端 bcrypt 加密存储） |

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
  "status": "success",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 400 | `邮箱不能为空` | email 未提供 |
| 400 | `密码不能为空` | password 未提供 |
| 400 | `邮箱 xxx@example.com 已注册` | 该邮箱已被注册 |

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
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_at": "2025-01-01 12:15:00",
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com"
    }
  }
}
```

| 字段 | 说明 |
|---|---|
| `access_token` | JWT 访问令牌 |
| `token_type` | 令牌类型，固定为 `"bearer"` |
| `expires_at` | 令牌过期时间，格式 `YYYY-MM-DD HH:MM:SS`（UTC） |
| `user.user_id` | 用户唯一标识 |
| `user.email` | 用户邮箱 |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 400 | `邮箱不能为空` | email 未提供 |
| 400 | `密码不能为空` | password 未提供 |
| 404 | `邮箱 xxx@example.com 未注册` | 该邮箱未注册 |
| 400 | `该账号通过 Google 登录注册，请使用 Google 登录` | 用户通过 Google OAuth 注册，未设置本地密码 |
| 401 | `密码错误` | 密码不正确 |

---

## 4. POST /upload — 上传视频

将视频文件上传到服务器，保存到本地并记录到数据库。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `multipart/form-data` |

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
  "status": "success",
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

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 400 | `不支持的文件类型` | 文件扩展名或 MIME 类型不在允许列表中 |

**服务端错误（附带 error code）：**

| HTTP 状态码 | data.code | 说明 |
|---|---|---|
| 500 | `PROBE_FAILED` | 视频元数据探测失败 |

---

## 5. POST /compress — 压缩视频

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
| `crf` | int | 否 | `32` | 恒定质量因子（0-51，值越小质量越高体积越大）。若设置 `target_v_bitrate` 则忽略此项 |
| `target_v_bitrate` | string | 否 | `null` | 目标视频码率，如 `"2M"`、`"1500k"`。设置后忽略 `crf`，使用固定码率编码 |
| `scale_width` | int | 否 | `null` | 缩放目标宽度（像素），高度等比缩放 |
| `max_fps` | int | 否 | `30` | 最大帧率限制 |
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

### 成功响应 (202)

压缩任务已提交，通过 `GET /task/{task_id}` 轮询结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
  }
}
```

任务完成后，`GET /task/{task_id}` 返回的 `result` 字段包含以下结构：

```json
{
  "asset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "source_asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "video",
  "path": "storage\\videos\\b2c3d4e5-f6a7-8901-bcde-f12345678901_compressed.mp4",
  "metadata": { ... }
}
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |

**服务端错误（附带 error code）：**

| HTTP 状态码 | data.code | 说明 |
|---|---|---|
| 500 | `FILE_MISSING` | 数据库记录存在但磁盘文件已丢失 |
| 500 | `COMPRESS_FAILED` | 视频压缩过程失败 |
| 500 | `PROBE_FAILED` | 压缩后视频的元数据提取失败 |

---

## 6. POST /analyze-script — 提取视频叙事结构

使用 AI 多模态模型对已上传的短视频进行叙事结构拆解，提取每个阶段（hook / setup / story / insight / cta / outro）的画面文字、音频文字和时间戳。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `asset_id` | string | **是** | 源视频的 asset_id（由 /upload 返回） |

### 请求示例

```json
{
  "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 成功响应 (202)

分析任务已提交，通过 `GET /task/{task_id}` 轮询结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd"
  }
}
```

任务完成后，`GET /task/{task_id}` 返回的 `result` 字段包含以下叙事结构：

```json
{
  "hook": {
    "visual_text": "你知道吗？90%的人都做错了这件事",
    "audio_text": "",
    "start_time": 0.0,
    "end_time": 5.2
  },
  "setup": { ... },
  "story": { ... },
  "insight": { ... },
  "cta": { ... },
  "outro": null
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `hook` | object \| null | 钩子阶段：开头抛出问题/悬念，抓住观众注意力 |
| `setup` | object \| null | 铺垫阶段：交代背景、设定情境 |
| `story` | object \| null | 正文阶段：故事主体/事件叙述/观点展开 |
| `insight` | object \| null | 金句阶段：核心观点/感悟/反转 |
| `cta` | object \| null | 行动号召阶段：引导互动（点赞/关注/转发） |
| `outro` | object \| null | 结尾阶段：收束/道别/落版文字 |

每个阶段对象包含以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `visual_text` | string | 该阶段画面上的核心叙事文字（不含水印、UI等无关文字） |
| `audio_text` | string | 该阶段的音频文本：旁白/台词/对话（纯 BGM 则为空字符串） |
| `start_time` | float | 该阶段开始时间（秒） |
| `end_time` | float | 该阶段结束时间（秒） |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |
| 403 | `无权访问该素材` | 素材不属于当前用户 |

**服务端错误（附带 error code）：**

| HTTP 状态码 | data.code | 说明 |
|---|---|---|
| 500 | `FILE_MISSING` | 数据库记录存在但磁盘文件已丢失 |
| 500 | `EXTRACT_FAILED` | AI 模型调用失败（通过 GET /task/{task_id} 查询 status: "failed" 获取详情） |

---

## 7. GET /task/{task_id} — 查询异步任务状态

查询由 `/compress` 或 `/analyze-script` 提交的异步任务的当前状态和结果。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | —（无请求体） |

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | **是** | 任务 ID（由发起接口返回） |

### 成功响应 (200)

**任务运行中：**

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "type": "analyze-script",
    "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "running",
    "created_at": "2025-01-01T12:00:00+00:00"
  }
}
```

**任务已完成：**

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "type": "analyze-script",
    "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "created_at": "2025-01-01T12:00:00+00:00",
    "result": { ... }
  }
}
```

**任务失败：**

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "type": "compress",
    "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "failed",
    "created_at": "2025-01-01T12:00:00+00:00",
    "error": "ffmpeg exited with code 1: ..."
  }
}
```

**任务已取消：**

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "type": "compress",
    "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "cancelled",
    "created_at": "2025-01-01T12:00:00+00:00"
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `task_id` | string | 任务唯一标识 |
| `type` | string | 任务类型：`compress` / `analyze-script` |
| `resource_id` | string | 关联的资源 ID（如 asset_id） |
| `status` | string | 任务状态：`running` / `completed` / `failed` / `cancelled` |
| `created_at` | string | 任务创建时间（ISO 8601） |
| `result` | any | （仅 `completed`）任务执行结果 |
| `error` | string | （仅 `failed`）错误描述 |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 403 | `无权访问该任务` | 试图查询其他用户的任务 |
| 404 | `任务 xxx 不存在` | task_id 不在注册表中 |

---

## 8. POST /task/{task_id}/cancel — 取消异步任务

取消一个正在执行的异步任务。取消后通过 `GET /task/{task_id}` 查询将返回 `status: "cancelled"`。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | —（无需请求体） |

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | **是** | 任务 ID（由发起接口返回） |

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/task/dddddddd-dddd-dddd-dddd-dddddddddddd/cancel \
  -H "Authorization: Bearer <token>"
```

### 成功响应 (200)

```json
{
  "status": "success",
  "data": "任务 dddddddd-dddd-dddd-dddd-dddddddddddd 已发起取消"
}
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 403 | `无权操作该任务` | 试图取消其他用户的任务 |
| 404 | `任务 xxx 不存在` | task_id 不在注册表中 |

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

### 客户端错误 (4xx) — 无 error code，直接通过 `message` 字段描述

| HTTP 状态码 | message | 触发场景 |
|---|---|---|
| 400 | `邮箱不能为空` | 注册/登录时未提供 email |
| 400 | `密码不能为空` | 注册/登录时未提供 password |
| 400 | `邮箱 xxx 已注册` | 注册时邮箱重复 |
| 400 | `该账号通过 Google 登录注册，请使用 Google 登录` | OAuth 用户尝试密码登录 |
| 400 | `不支持的文件类型` | 上传了非视频文件 |
| 400 | `缺少 asset_id 参数` | 压缩/提取时未提供 asset_id |
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT payload 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应用户已被删除 |
| 401 | `密码错误` | 登录密码不匹配 |
| 403 | `无权访问该素材` | 尝试操作不属于自己的素材 |
| 403 | `无权操作该任务` | 试图取消其他用户的任务 |
| 404 | `邮箱 xxx 未注册` | 登录时邮箱不存在 |
| 404 | `素材 xxx 不存在` | asset_id 对应记录不存在 |
| 404 | `任务 xxx 不存在` | task_id 不在注册表中 |

### 服务端错误 (5xx) — 附带 `data.code` 和 `data.details`

| data.code | HTTP 状态码 | 说明 |
|---|---|---|
| `PROBE_FAILED` | 500 | 视频元数据探测失败（上传后或压缩后） |
| `FILE_MISSING` | 500 | Asset 记录存在但磁盘文件丢失 |
| `COMPRESS_FAILED` | 500 | 视频压缩失败 |
| `EXTRACT_FAILED` | 500 | AI 模型调用失败 |

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

## 附录 D: 异步任务与取消

### 概述

视频压缩 (`/compress`) 和 AI 分析 (`/analyze-script`) 是长时异步操作。这些端点采用 **fire-and-forget** 模式：发起接口立即返回 `task_id`，客户端通过轮询 `GET /task/{task_id}` 获取进度和结果。

### 工作流程

```
POST /compress       → 202 { task_id }     ← 立即返回
GET  /task/{id}      → 200 { status: "running" }
GET  /task/{id}      → 200 { status: "completed", result: {...} }  ← 结果就绪
POST /task/{id}/cancel  → 200 "已发起取消"   ← 中途取消
GET  /task/{id}      → 200 { status: "cancelled" }
```

### 任务状态

| 状态 | 说明 |
|---|---|
| `running` | 任务正在执行 |
| `completed` | 任务成功完成，`result` 字段包含结果数据 |
| `failed` | 任务执行失败，`error` 字段包含错误详情 |
| `cancelled` | 任务已被取消 |

### 取消机制

- **`/compress`**: 底层 `ffmpeg` 子进程被 `SIGKILL` 杀死，部分压缩文件被清理
- **`/analyze-script`**: 底层异步 HTTP 请求的 TCP 连接被关闭，API 调用立即中止

### 注意事项

- 发起接口仅做参数校验（asset 是否存在、归属等），通过校验后立即返回 202
- 任务记录在服务内存中持久保存，服务重启后丢失
- 取消操作是尽力而为的——AI 模型可能已经消耗了部分 token
- 建议客户端以 1-2 秒间隔轮询 `GET /task/{task_id}`
