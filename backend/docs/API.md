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
  - [4. POST /upload — 上传文件](#4-post-upload--上传文件)
    - [请求参数](#请求参数-3)
    - [请求示例 (curl)](#请求示例-curl)
    - [成功响应 (201)](#成功响应-201-1)
    - [错误响应](#错误响应-2)
  - [5. POST /compress — 压缩视频](#5-post-compress--压缩视频)
    - [请求参数](#请求参数-4)
    - [请求示例](#请求示例-2)
    - [成功响应 (202)](#成功响应-202)
    - [错误响应](#错误响应-3)
  - [6. POST /analyze-script — 提取视频叙事结构](#6-post-analyze-script--提取视频叙事结构)
    - [请求参数](#请求参数-5)
    - [请求示例](#请求示例-3)
    - [成功响应 (202)](#成功响应-202-1)
    - [响应字段说明](#响应字段说明)
    - [错误响应](#错误响应-4)
  - [7. POST /analyze-visual — 视频视觉层分析](#7-post-analyze-visual--视频视觉层分析)
    - [请求参数](#请求参数-6)
    - [请求示例](#请求示例-4)
    - [成功响应 (202)](#成功响应-202-2)
    - [响应字段说明](#响应字段说明-1)
    - [错误响应](#错误响应-5)
  - [8. GET /task/{task\_id}/stream — SSE 实时推送任务状态（推荐）](#8-get-tasktask_idstream--sse-实时推送任务状态推荐)
    - [路径参数](#路径参数-1)
    - [请求示例](#请求示例-5)
    - [响应格式 (SSE)](#响应格式-sse)
    - [SSE 事件说明](#sse-事件说明)
    - [错误响应](#错误响应-7)
  - [9. POST /task/{task\_id}/cancel — 取消异步任务](#9-post-tasktask_idcancel--取消异步任务)
    - [路径参数](#路径参数-2)
    - [请求示例](#请求示例-6)
    - [成功响应 (200)](#成功响应-200-2)
    - [错误响应](#错误响应-8)
  - [10. POST /analyze-audio — 异步音频分析](#10-post-analyze-audio--异步音频分析)
    - [请求参数](#请求参数-7)
    - [请求示例](#请求示例-7)
    - [成功响应 (202)](#成功响应-202-3)
    - [获取分析结果](#获取分析结果)
    - [任务完成后 result 结构](#任务完成后-result-结构)
    - [result 字段说明](#result-字段说明)
    - [前端集成示例](#前端集成示例)
    - [错误响应](#错误响应-9)
  - [11. GET /files/{asset\_id} — 访问素材文件](#11-get-filesasset_id--访问素材文件)
    - [路径参数](#路径参数-3)
    - [请求示例](#请求示例-8)
    - [安全校验](#安全校验)
    - [成功响应](#成功响应)
    - [错误响应](#错误响应-10)
  - [12. POST /split — 视频切割](#12-post-split--视频切割)
    - [请求参数](#请求参数-8)
    - [请求示例](#请求示例-9)
    - [成功响应 (202)](#成功响应-202-4)
    - [任务结果结构](#任务结果结构)
    - [错误响应](#错误响应-11)
  - [13. POST /analyze-effect — 视频特效分析](#13-post-analyze-effect--视频特效分析)
    - [请求参数](#请求参数-9)
    - [请求示例](#请求示例-10)
    - [成功响应 (202)](#成功响应-202-5)
    - [响应字段说明](#响应字段说明-3)
    - [错误响应](#错误响应-12)
  - [14. GET / PATCH /effects — 查询与编辑特效](#14-get--patch-effects--查询与编辑特效)
    - [14.1 GET /effects — 查询特效库](#141-get-effects--查询特效库)
    - [14.2 PATCH /effects — 校正任务特效](#142-patch-effects--校正任务特效)
    - [14.3 GET /effects/demo/{filename} — 获取特效 Demo 视频](#143-get-effectsdemofilename--获取特效-demo-视频)
  - [15. POST /plan — 生成视频模板](#15-post-plan--生成视频模板)
    - [请求参数](#请求参数-10)
    - [请求示例](#请求示例-11)
    - [成功响应 (202)](#成功响应-202-6)
    - [通过 SSE / 轮询获取模板](#通过-sse--轮询获取模板)
    - [错误响应](#错误响应-13)
  - [16. PATCH /plan/{plan\_id}/slot/{slot\_id} — 填充模板槽位](#16-patch-planplan_idslotslot_id--填充模板槽位)
    - [路径参数](#路径参数-4)
    - [请求参数](#请求参数-11)
    - [响应示例](#响应示例-1)
    - [错误响应](#错误响应-14)
  - [17. POST /plan/{plan\_id}/generate — 批量 AI 生成槽位内容](#17-post-planplan_idgenerate--批量-ai-生成槽位内容)
    - [路径参数](#路径参数-5)
    - [成功响应 (202)](#成功响应-202-7)
    - [通过 SSE / 轮询获取结果](#通过-sse--轮询获取结果)
    - [生成逻辑](#生成逻辑)
    - [错误响应](#错误响应-15)
  - [18. POST /render — 渲染视频](#18-post-render--渲染视频)
    - [请求参数](#请求参数-12)
    - [请求示例](#请求示例-12)
    - [成功响应 (202)](#成功响应-202-8)
    - [通过 SSE / 轮询获取渲染进度](#通过-sse--轮询获取渲染进度)
    - [任务结果结构](#任务结果结构-1)
    - [渲染流程](#渲染流程)
    - [错误响应](#错误响应-16)
  - [附录 B: 错误码参考](#附录-b-错误码参考)
    - [客户端错误 (4xx) — 无 error code，直接通过 `message` 字段描述](#客户端错误-4xx--无-error-code直接通过-message-字段描述)
    - [服务端错误 (5xx) — 附带 `data.code` 和 `data.details`](#服务端错误-5xx--附带-datacode-和-datadetails)
  - [附录 C: 支持的视频格式](#附录-c-支持的视频格式)
  - [附录 D: 异步任务与取消](#附录-d-异步任务与取消)
    - [概述](#概述)
    - [工作流程](#工作流程)
    - [任务状态](#任务状态)
    - [取消机制](#取消机制)
    - [注意事项](#注意事项)

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

## 4. POST /upload — 上传文件

将视频或图片文件上传到服务器，保存到本地并记录到数据库。按文件扩展名自动识别类型。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `multipart/form-data` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | 是 | 视频或图片文件（视频格式见附录 C，图片格式见下方） |

**支持的图片格式：**

| 扩展名 | MIME 类型 |
|---|---|
| `.jpg` / `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.webp` | `image/webp` |
| `.bmp` | `image/bmp` |

### 请求示例 (curl)

```bash
# 上传视频
curl -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/video.mp4"

# 上传图片
curl -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.png"
```

### 成功响应 (201)

**视频上传：**

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
    },
    "cover_image_asset_id": "d1d1d1d1-d1d1-d1d1-d1d1-d1d1d1d1d1d1"
  }
}
```

**图片上传：**

```json
{
  "status": "success",
  "data": {
    "asset_id": "e1e1e1e1-e1e1-e1e1-e1e1-e1e1e1e1e1e1",
    "type": "image",
    "path": "storage\\images\\e1e1e1e1-e1e1-e1e1-e1e1-e1e1e1e1e1e1.png",
    "metadata": {
      "filepath": "D:\\HKU\\...\\storage\\images\\e1e1....png",
      "width": 1920,
      "height": 1080,
      "size": 524288,
      "format": "PNG"
    }
  }
}
```

> **视频封面自动提取**：上传视频完成后自动提取封面图。上传图片时不附带封面。`cover_image_asset_id` 仅视频上传时有。`metadata` 结构按文件类型不同而不同。

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
| 500 | `PROBE_FAILED` | 文件元数据探测失败 |

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

压缩任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
  }
}
```

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段包含以下结构：

```json
{
  "asset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "source_asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "video",
  "path": "storage\\videos\\b2c3d4e5-f6a7-8901-bcde-f12345678901_compressed.mp4",
  "metadata": { ... },
  "cover_image_asset_id": "e1e1e1e1-e1e1-e1e1-e1e1-e1e1e1e1e1e1"
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

分析任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd"
  }
}
```

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段包含以下叙事结构：

```json
{
  "narrator_perspective": "first_person",
  "narrator_perspective_note": null,
  "stages": {
    "hook": {
      "visual_text": "你知道吗？90%的人都做错了这件事",
      "audio_text": "",
      "start_time": 0.0,
      "end_time": 5.2,
      "emotional_tone": "suspenseful",
      "hook_type": "pain_point",
      "cta_type": null
    },
    "setup": {
      "visual_text": "我花了三年时间研究这个问题",
      "audio_text": "",
      "start_time": 5.2,
      "end_time": 10.0,
      "emotional_tone": "neutral",
      "hook_type": null,
      "cta_type": null
    },
    "story": {
      "visual_text": "第一天...\n第二天...\n第三天...",
      "audio_text": "",
      "start_time": 10.0,
      "end_time": 38.5,
      "emotional_tone": "positive",
      "hook_type": null,
      "cta_type": null
    },
    "insight": {
      "visual_text": "人生最大的智慧，就是活在当下",
      "audio_text": "",
      "start_time": 38.5,
      "end_time": 45.0,
      "emotional_tone": "positive",
      "hook_type": null,
      "cta_type": null
    },
    "cta": {
      "visual_text": "点赞收藏，转发给你关心的人",
      "audio_text": "",
      "start_time": 45.0,
      "end_time": 50.0,
      "emotional_tone": "positive",
      "hook_type": null,
      "cta_type": "share_spread"
    },
    "outro": null
  }
}
```

### 响应字段说明

**顶层字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `narrator_perspective` | string \| null | 全局叙述视角：`first_person` / `second_person` / `third_person` / `mixed` |
| `narrator_perspective_note` | string \| null | 仅 `mixed` 时的视角切换说明，其余为 `null` |
| `stages` | object | 6 个叙事阶段的容器 |

**`stages` 的 6 个阶段字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `hook` | object \| null | 钩子阶段：开头抛出问题/悬念，抓住观众注意力 |
| `setup` | object \| null | 铺垫阶段：交代背景、设定情境 |
| `story` | object \| null | 正文阶段：故事主体/事件叙述/观点展开 |
| `insight` | object \| null | 金句阶段：核心观点/感悟/反转 |
| `cta` | object \| null | 行动号召阶段：引导互动（点赞/关注/转发） |
| `outro` | object \| null | 结尾阶段：收束/道别/落版文字 |

**每个阶段对象包含以下字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `visual_text` | string | 该阶段画面上的核心叙事文字（不含水印、UI等无关文字） |
| `audio_text` | string | 该阶段的音频文本：旁白/台词/对话（纯 BGM 则为空字符串） |
| `start_time` | float | 该阶段开始时间（秒） |
| `end_time` | float | 该阶段结束时间（秒） |
| `emotional_tone` | string \| null | 情绪基调：`positive` / `negative` / `neutral` / `suspenseful` / `curious` / `urgent` / `humorous` / `calm` |
| `hook_type` | string \| null | 钩子类型（仅 hook 阶段）：`pain_point` / `suspense` / `result_first` / `counter_intuitive` / `number_shock` / `identity_lock` / `scene_immersion` / `contrast_flip` |
| `cta_type` | string \| null | 行动号召类型（仅 cta 阶段）：`follow` / `like_collect` / `comment` / `purchase` / `discount_hook` / `dm_funnel` / `share_spread` / `challenge` |

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
| 500 | `EXTRACT_FAILED` | AI 模型调用失败（通过 `GET /task/{task_id}/stream` 查询 `status: "failed"` 获取详情） |

---

## 7. POST /analyze-visual — 视频视觉层分析

使用 AI 多模态模型对已上传的短视频进行视觉层面结构化拆解，提取镜头切分、转场类型、运镜方式、文字元素，并生成节奏摘要。

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

分析任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
  }
}
```

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段包含以下视觉分析结果：

```json
{
  "total_duration": 60.5,
  "pacing": {
    "avg_shot_duration": 2.3,
    "pacing_category": "fast",
    "acceleration_points": [12.5, 35.0]
  },
  "shots": [
    {
      "shot_index": 1,
      "start_time": 0.0,
      "end_time": 2.5,
      "camera_movement": "zoom_in",
      "is_text_frame": false,
      "description": "片头标题大字弹出，伴随背景画面"
    },
    {
      "shot_index": 2,
      "start_time": 2.5,
      "end_time": 4.0,
      "camera_movement": "static",
      "is_text_frame": true,
      "description": "纯色背景上的白色大字叙事文字"
    }
  ],
  "transitions": [
    {
      "after_shot_index": 1,
      "type": "dissolve",
      "duration": 0.3
    }
  ],
  "text_elements": [
    {
      "text": "你知道吗？90%的人都做错了这件事",
      "position": "center",
      "appear_time": 0.3,
      "disappear_time": 2.5
    }
  ],
  "text_density_curve": [
    { "time": 0.3, "text_count": 1 },
    { "time": 2.5, "text_count": 0 }
  ]
}
```

### 响应字段说明

**顶层字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `total_duration` | float | 视频总时长（秒） |
| `pacing` | object | 全局节奏摘要 |
| `shots` | array | 镜头列表，按时间顺序排列 |
| `transitions` | array | 转场列表，长度应为 `len(shots)-1` |
| `text_elements` | array | 独立文字时间轴，元素可跨镜头，不嵌套在 ShotInfo 内 |
| `text_density_curve` | array | 文字密度曲线，由后处理代码计算填充（非 LLM 输出） |

**`pacing` 对象字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `avg_shot_duration` | float | 平均镜头时长（秒） |
| `pacing_category` | string | 节奏档位：`fast`（<2s）/ `medium`（2-4s）/ `slow`（>4s） |
| `acceleration_points` | array[float] | 节奏骤然加快的时间点列表（秒），通常对应高潮段入口 |

**`shots` 数组元素字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `shot_index` | int | 镜头序号，从 1 开始，仅用于展示，非数组下标 |
| `start_time` | float | 镜头开始时间（秒） |
| `end_time` | float | 镜头结束时间（秒） |
| `camera_movement` | string \| null | 镜头运动类型：`static` / `zoom_in` / `zoom_out` / `pan` / `tilt` / `handheld` |
| `is_text_frame` | bool | 该镜头是否为纯文字帧（无视频素材，仅文字+纯色背景） |
| `description` | string | 镜头画面简述，10-30字 |

**`transitions` 数组元素字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `after_shot_index` | int | 转场发生在第 N 个镜头之后（对应 shot_index） |
| `type` | string | 转场类型：`cut` / `dissolve` / `wipe` / `fade_in` / `fade_out` / `slide` / `zoom` / `glitch` / `rgb_split` |
| `duration` | float | 转场持续时长（秒），硬切为 0.0 |

**`text_elements` 数组元素字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `text` | string | 文字内容 |
| `position` | string \| null | 屏幕位置：`top_center` / `center` / `bottom_center` / `overlay_left` / `overlay_right` / `full_screen` |
| `appear_time` | float | 文字出现时间（秒） |
| `disappear_time` | float | 文字消失时间（秒） |

**`text_density_curve` 数组元素字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `time` | float | 采样时间点（秒） |
| `text_count` | int | 该时刻屏幕上同时存在的文字数量 |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 400 | `视频文件过大（xx MB），超过分析上限 xx MB。请先调用 /compress 压缩后再分析。` | 视频文件超过 `MAX_ANALYZE_SIZE_MB` 限制 |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |
| 403 | `无权访问该素材` | 素材不属于当前用户 |

**服务端错误（附带 error code）：**

| HTTP 状态码 | data.code | 说明 |
|---|---|---|
| 500 | `FILE_MISSING` | 数据库记录存在但磁盘文件已丢失 |
| 500 | `EXTRACT_FAILED` | AI 模型调用失败（通过 `GET /task/{task_id}/stream` 查询 `status: "failed"` 获取详情） |

---

## 8. GET /task/{task_id}/stream — SSE 实时推送任务状态（推荐）

使用 **Server-Sent Events (SSE)** 实时订阅任务状态变更，无需反复轮询。连接建立后立即推送当前状态；若任务仍在运行，期间每 15 秒发送一次 keepalive 注释保持连接；任务终止时推送最终状态后自动关闭连接。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | —（无请求体） |
| **响应类型** | `text/event-stream`（SSE 流式推送） |

> **推荐**：此端点比轮询更高效。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | **是** | 任务 ID（由发起接口返回） |

### 请求示例

```bash
curl -N "http://127.0.0.1:8000/task/dddddddd-dddd-dddd-dddd-dddddddddddd/stream" \
  -H "Authorization: Bearer <token>"
```

### 响应格式 (SSE)

**任务已完成/失败/取消（连接时任务已结束）：**

推送一条最终状态后立即关闭连接：

```
data: {"task_id":"dddddddd-...","type":"analyze-script","resource_id":"a1b2...","status":"completed","created_at":"...","result":{...}}
```

**任务运行中（连接时任务仍在执行）：**

普通任务（compress/analyze-script/visual/effect）先推送运行状态，然后每 15 秒发送 keepalive，最后推送最终状态：

```
data: {"task_id":"dddddddd-...","status":"running"}

: keepalive

: keepalive

data: {"task_id":"dddddddd-...","type":"analyze-script","resource_id":"a1b2...","status":"completed","created_at":"...","result":{...}}
```

> **流式数据（已弃用）**：`analyze-audio` 曾使用 SSE 逐帧推送音频特征。现已改为与其他分析接口一致的一次性结果返回。`build_event_stream` 中保留的 `_stream_queue` 消费逻辑可供未来的流式任务复用，当前无活跃的流式任务。

### SSE 事件说明

| 帧类型 | 格式 | 说明 |
|---|---|---|
| 初始状态 | `data: <json>\n\n` | 连接建立后立即发送的第一帧：若任务已结束则包含完整 `to_dict()` 输出；若仍在运行则只包含 `{"task_id":"...","status":"running"}` |
| 流式数据 | `data: <json>\n\n` | （仅流式任务）任务运行期间逐帧推送的业务数据，格式取决于任务类型（当前无活跃的流式任务） |
| keepalive | `: keepalive\n\n` | 以 `:` 开头的 SSE 注释行，仅用于保持 TCP 连接不被中间代理关闭，无业务含义，客户端可直接忽略 |
| 最终状态 | `data: <json>\n\n` | 任务状态转为 `completed` / `failed` / `cancelled` 时发送的最后一帧，包含完整 `to_dict()` 输出，此帧后服务端关闭连接 |

**任务在不同状态下首次连接的 SSE 行为：**

| 任务当前状态 | SSE 流行为 |
|---|---|
| `running`（普通任务） | 发送 `{"task_id":"...","status":"running"}`，每 15 秒 keepalive，状态变更后发送最终 `to_dict()` 并关闭 |
| `running`（流式任务） | 发送 `{"task_id":"...","status":"running"}`，逐帧推送业务数据（帧间超时 15s 则发 keepalive），任务完成后发送最终 `to_dict()` 并关闭 |
| `completed` | 发送最终 `to_dict()` 后立即关闭 |
| `failed` | 发送最终 `to_dict()`（含 `error` 字段）后立即关闭 |
| `cancelled` | 发送最终 `to_dict()` 后立即关闭 |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 403 | `无权访问该任务` | 试图访问其他用户的任务 |
| 404 | `任务 xxx 不存在` | task_id 不在注册表中 |

---

## 9. POST /task/{task_id}/cancel — 取消异步任务

取消一个正在执行的异步任务。取消后通过 `GET /task/{task_id}/stream` 查询将返回 `status: "cancelled"`。

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

## 10. POST /analyze-audio — 异步音频分析

对已上传的视频进行音频分析：提取背景音乐（BGM）并使用 librosa 一次性提取全局音频特征（BPM、节拍时间点、能量曲线等）。采用与 `/compress`、`/analyze-script`、`/analyze-visual` 一致的异步任务模式。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

> **BGM 自动提取**：后台任务使用 `ffmpeg` 从视频中提取音轨，再用 `audio_separator` (UVR-MDX-NET-Inst_HQ_3) 分离人声与伴奏，仅保留伴奏（bgm.wav）用于分析。分离后的 bgm.wav 以 `type="audio"` 存入数据库。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `asset_id` | string | **是** | 源视频的 asset_id（由 `/upload` 返回） |

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/analyze-audio \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}'
```

### 成功响应 (202)

分析任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取最终结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "ffffffff-ffff-ffff-ffff-ffffffffffff"
  }
}
```

---

### 获取分析结果

与其他分析接口（`/analyze-script`、`/analyze-visual` 等）一致，通过统一的任务接口获取结果：

```
GET /task/{task_id}/stream
```

或通过 SSE 获取完成通知：

```
GET /task/{task_id}/stream
```

### 任务完成后 result 结构

```json
{
  "task_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "type": "analyze-audio",
  "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "created_at": "2025-01-01T12:00:00+00:00",
  "result": {
    "audio_asset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "bgm_path": "storage/audios/b2c3d4e5-..._bgm.wav",
    "duration": 30.8,
    "genre": "pop",
    "bpm": 120.0,
    "beat_timings": [0.0, 0.50, 1.00, 1.50, 2.00, 2.50, 3.00],
    "energy_curve": [0.0456, 0.0512, 0.0489, 0.0623, 0.0711],
    "spectral_centroid": [1256.3, 1270.1, 1243.8, 1288.5, 1262.0],
    "spectral_centroid_mean": 1256.3,
    "spectral_flux": [0.0, 8.92, 7.34, 12.45, 6.78],
    "onset_envelope": [0.0012, 0.0034, 0.0021, 0.0056, 0.0018],
    "dynamic_range": 0.0023
  }
}
```

### result 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `audio_asset_id` | string | BGM 音频的 asset_id，可用于下载 |
| `bgm_path` | string | BGM 文件在服务器上的路径 |
| `duration` | float | 音频总时长（秒） |
| `genre` | string | 音乐流派分类（HuggingFace） |
| `bpm` | float | librosa 节拍追踪 BPM |
| `beat_timings` | float[] | 所有重拍时间点列表（秒），按时间升序 |
| `energy_curve` | float[] | librsa RMS 能量曲线，每帧一个值 |
| `spectral_centroid` | float[] | 逐帧频谱质心（Hz），长度与 energy_curve 一致 |
| `spectral_centroid_mean` | float | 全局平均频谱质心（Hz） |
| `spectral_flux` | float[] | 逐帧频谱变化率，反映新声音出现 |
| `onset_envelope` | float[] | 逐帧 onset 强度包络值 |
| `dynamic_range` | float | 全局动态范围（max − min RMS） |

---

### 前端集成示例

```javascript
// 步骤 1：发起音频分析
const { task_id } = await fetch("http://127.0.0.1:8000/analyze-audio", {
  method: "POST",
  headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ asset_id: "a1b2c3d4-..." }),
}).then(r => r.json()).then(d => d.data);

// 步骤 2：轮询任务结果
const poll = async () => {
  const res = await fetch(
    `http://127.0.0.1:8000/task/${task_id}`,
    { headers: { Authorization: "Bearer <token>" } }
  );
  const data = await res.json();
  if (data.result) {
    console.log("分析完成:", data.result);
    console.log("BPM:", data.result.bpm);
    console.log("节拍时间点:", data.result.beat_timings);
  } else if (data.status === "failed") {
    console.error("分析失败:", data.error);
  } else {
    setTimeout(poll, 1000);  // 1s 后重试
  }
};
poll();
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 400 | `不支持的文件类型 .xxx` | 文件扩展名不在允许列表中 |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |
| 403 | `无权访问该素材` | 素材不属于当前用户 |
| 500 | `源文件丢失` | 数据库记录存在但磁盘文件已丢失 |

若分析开始后发生运行时错误，任务状态变为 `failed`，通过 `GET /task/{task_id}/stream` 的 `error` 字段获取详情。

---

## 11. GET /files/{asset_id} — 访问素材文件

通过 `asset_id` 直接访问已上传的素材文件。服务端自动校验归属权限，返回文件二进制流。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | —（无请求体） |
| **响应类型** | `application/octet-stream` 或对应文件 MIME 类型 |

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `asset_id` | string | **是** | 素材的 asset_id（由 `/upload`、`/compress`、`/split`、`/analyze-audio` 等接口返回） |

### 请求示例

```bash
# 下载原始视频
curl "http://127.0.0.1:8000/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer <token>" \
  -o video.mp4

# 下载压缩视频
curl "http://127.0.0.1:8000/files/b2c3d4e5-f6a7-8901-bcde-f12345678901" \
  -H "Authorization: Bearer <token>"

# 下载 BGM 音频
curl "http://127.0.0.1:8000/files/c3d4e5f6-a7b8-9012-cdef-234567890123" \
  -H "Authorization: Bearer <token>"

# 下载封面图
curl "http://127.0.0.1:8000/files/d1d1d1d1-d1d1-d1d1-d1d1-d1d1d1d1d1d1" \
  -H "Authorization: Bearer <token>"
```

### 安全校验

| 校验步骤 | 说明 |
|---|---|
| 数据库查询 | `Asset.asset_id == asset_id` 查库，记录不存在 → 404 |
| 权限校验 | `asset.user_id == current_user.user_id`，不属于 → 403 `无权访问该文件` |
| 文件存在 | `Path(asset.path).exists()`，丢失 → 500 `文件丢失` |

> **`storage/tmp` 下的中间文件（ffmpeg 临时产物、Separator 工作文件等）没有对应的 Asset 记录，无法通过此接口访问。**

### 成功响应

直接返回文件二进制流，`Content-Type` 根据文件扩展名自动设置。

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 403 | `无权访问该文件` | 素材不属于当前用户 |
| 404 | `文件不存在` | asset_id 无对应记录 |
| 500 | `文件丢失` | asset 记录存在但磁盘文件已丢失 |

---

## 12. POST /split — 视频切割

对已上传的视频进行场景切分，支持两种检测方式：基于 `scenedetect` 的程序化检测（默认）或基于多模态 LLM 的语义切割。切割后的每个片段保存为独立 Asset，通过 `/files/{asset_id}` 访问。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `asset_id` | string | **是** | — | 源视频的 asset_id（由 `/upload` 返回） |
| `use_ai` | bool | 否 | `false` | 是否使用 LLM 进行语义切割；`false` 使用 scenedetect ContentDetector |
| `threshold` | float | 否 | `25.0` | ContentDetector 灵敏度阈值（仅 `use_ai: false` 时生效） |
| `min_scene_len` | int | 否 | `15` | 最小场景长度（帧数，仅 `use_ai: false` 时生效） |

> **两种检测方式对比：**
>
> | | scenedetect (`use_ai: false`) | AI (`use_ai: true`) |
> |---|---|---|
> | 原理 | 逐帧内容差异 (`content_val`) | LLM 多模态语义理解 |
> | 速度 | 快（秒级） | 慢（取决于模型响应） |
> | 切割依据 | 画面变化幅度 | 特效对象边界 |
> | 输出 | `cut_score`（置信度） | `reason`（切割原因） |

### 请求示例

```bash
# scenedetect 方式（默认）
curl -X POST http://127.0.0.1:8000/split \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "a1b2c3d4-..."}'

# AI 方式
curl -X POST http://127.0.0.1:8000/split \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "a1b2c3d4-...", "use_ai": true}'

# 自定义 scenedetect 参数
curl -X POST http://127.0.0.1:8000/split \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "a1b2c3d4-...", "threshold": 20.0, "min_scene_len": 30}'
```

### 成功响应 (202)

切割任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "gggggggg-gggg-gggg-gggg-gggggggggggg"
  }
}
```

### 任务结果结构

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段包含以下结构：

```json
{
  "source_asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "scenedetect",
  "total_segments": 5,
  "segments": [
    {
      "index": 0,
      "start_sec": 0.0,
      "end_sec": 3.2,
      "duration": 3.2,
      "cut_score": 12.5
    },
    {
      "index": 1,
      "start_sec": 3.2,
      "end_sec": 7.8,
      "duration": 4.6,
      "cut_score": 8.3
    }
  ],
  "clip_assets": [
    {
      "asset_id": "c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1",
      "index": 0,
      "path": "storage/videos/c1c1c1c1-..._000.mp4",
      "metadata": {
        "filepath": "D:\\...\\storage\\videos\\c1c1..._000.mp4",
        "codec": "h264",
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "duration": 3.2
      },
      "cover_image_asset_id": "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `source_asset_id` | string | 源视频 asset_id |
| `method` | string | 切割方式：`scenedetect` 或 `ai` |
| `total_segments` | int | 切割出的片段总数 |
| `segments[].index` | int | 片段序号（从 0 开始） |
| `segments[].start_sec` | float | 片段开始时间（秒） |
| `segments[].end_sec` | float | 片段结束时间（秒） |
| `segments[].duration` | float | 片段时长（秒） |
| `segments[].cut_score` | float \| null | 切割点置信度（仅 scenedetect） |
| `segments[].reason` | string \| null | 切割原因（仅 AI） |
| `clip_assets[].asset_id` | string | 片段对应的 Asset ID，可通过 `/files/{asset_id}` 下载 |

| `clip_assets[].path` | string | 片段文件路径 |
| `clip_assets[].metadata` | object | 片段视频元数据（同 VideoMeta） |
| `clip_assets[].cover_image_asset_id` | string \| null | 片段封面图的 Asset ID，可通过 `/files/{uuid}` 下载；提取失败时为 `null` |

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |
| 403 | `无权访问该素材` | 素材不属于当前用户 |
| 500 | `源文件丢失` | 数据库记录存在但磁盘文件已丢失 |

运行时错误（如 ffmpeg 切割失败）通过任务 `status: "failed"` 的 `error` 字段返回。

---

## 13. POST /analyze-effect — 视频特效分析

使用 AI 多模态模型分析视频中包含的 UI/动效设计视觉特效，匹配内置特效库识别特效类型。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `asset_id` | string | **是** | 源视频的 asset_id（由 `/upload` 返回） |

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/analyze-effect \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}'
```

### 成功响应 (202)

分析任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh"
  }
}
```

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段包含以下特效分析结果：

```json
{
  "observations": "视频开头出现大字标题，以逐字弹出的方式出现，伴有缩放动效。中段有快速的光效闪过转场。背景有噪点纹理覆盖。结尾文字淡出消失。",
  "effects": [
    {
      "name": "Typewriter Text",
      "evidence": "标题文字逐字出现，有打字机光标效果"
    },
    {
      "name": "Pop Entry",
      "evidence": "文字以缩放弹出方式进入画面"
    },
    {
      "name": "Light Leak Transition",
      "evidence": "镜头切换时出现快速光效闪过"
    },
    {
      "name": "Film Grain Overlay",
      "evidence": "画面全程覆盖细微噪点纹理"
    }
  ]
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `observations` | string | 对视频中所有视觉现象的自由形式描述（模型在匹配特效库之前先进行纯观察），聚焦于视觉呈现的"如何"而非内容"是什么" |
| `effects` | array | 匹配到的特效列表，仅包含有明确视觉证据的特效 |
| `effects[].name` | string | 特效名称，与内置特效库中的名称精确匹配 |
| `effects[].evidence` | string | 支持该匹配的具体视觉现象描述（≤20词） |

> **内置特效库**：模型从 `src/lib/components_description.json` 加载特效库，按类别（文字动效、转场、画面效果等）分组，仅识别库中已定义的特效类型。每个匹配必须基于观察中的具体视觉现象作为证据，宁可少报也不误报。

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |
| 401 | `令牌格式无效` | JWT 缺少 user_id |
| 401 | `用户不存在或已注销` | 令牌对应的用户已被删除 |
| 400 | `缺少 asset_id 参数` | 请求体未提供 asset_id |
| 400 | `视频文件过大（xx MB），超过分析上限 xx MB。请先调用 /compress 压缩后再分析。` | 视频文件超过 `MAX_ANALYZE_SIZE_MB` 限制 |
| 404 | `素材 xxx 不存在` | 该 asset_id 对应的记录不存在 |
| 403 | `无权访问该素材` | 素材不属于当前用户 |

**服务端错误（附带 error code）：**

| HTTP 状态码 | data.code | 说明 |
|---|---|---|
| 500 | `FILE_MISSING` | 数据库记录存在但磁盘文件已丢失 |
| 500 | `EXTRACT_FAILED` | AI 模型调用失败（通过 `GET /task/{task_id}/stream` 查询 `status: "failed"` 获取详情） |

---

## 14. GET / PATCH /effects — 查询与编辑特效

### 14.1 GET /effects — 查询特效库

获取所有可用的视觉特效组件列表，支持模糊搜索。

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 需要（Bearer Token） |

> **数据来源**：`Effect` 表在服务启动时从 `components_description.json` 自动初始化（59 个 remocn 组件），后续通过此接口查询。

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `q` | string | 否 | 模糊搜索关键词，匹配 name、category、description 三个字段。省略时返回全部 59 条 |

#### 请求示例

```bash
curl "http://127.0.0.1:8000/effects?q=blur" \
  -H "Authorization: Bearer <token>"
```

```bash
curl "http://127.0.0.1:8000/effects" \
  -H "Authorization: Bearer <token>"
```

#### 成功响应 (200)

```json
{
  "status": "success",
  "data": [
    {
      "name": "BlurReveal",
      "category": "Typography",
      "description": "文字从严重模糊聚焦至锐利，由虚到实单次进场。...",
      "demo_path": null
    },
    {
      "name": "FrostedGlassWipe",
      "category": "Transitions",
      "description": "磨砂玻璃面板从画面一侧滑过遮旧场景露新场景。...",
      "demo_path": "/effects/demo/frosted-glass-wipe.mp4"
    }
  ]
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 组件唯一名称（59 个白名单内） |
| `category` | string | 分类：Typography / Core Primitives / Environment & Lighting / UI Blocks / Transitions / Compositions |
| `description` | string | 中文功能描述 |
| `demo_path` | string \| null | 特效 Demo 视频的 URL 路径，前端使用时需加 `/api` 前缀；无 Demo 视频时为 `null` |

#### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 401 | `令牌已过期或无效` | JWT 解码失败 |

### 14.2 PATCH /effects — 校正任务特效

修改已完成 `/analyze-effect` 任务的 effects 列表。前端在查看 AI 分析结果后可删除误判或补充遗漏的特效，修正后的列表会被 `/plan` 端点消费。

| 属性 | 值 |
|---|---|
| **方法** | `PATCH` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

> **约束**：只能修改 `type=analyze-effect` 且 `status=completed` 的任务。`task.result.effects` 被全量替换（不在新列表中的被删除，新增的在列表中）。修改直接在内存中生效，`observations` 字段不可修改。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | **是** | `/analyze-effect` 返回的 task_id |
| `effects` | array | **是** | 用户校正后的完整 effects 列表（**替换**原有列表） |

`effects[]` 元素:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | **是** | 特效名称（不强制 59 白名单，用户可自由命名） |
| `evidence` | string | **是** | 视频中观察到该特效的具体视觉证据 |

#### 请求示例

```bash
curl -X PATCH http://127.0.0.1:8000/effects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "uuid-of-analyze-effect-task",
    "effects": [
      {"name": "BlurReveal", "evidence": "文字从模糊到清晰"},
      {"name": "Typewriter", "evidence": "逐字出现效果"},
      {"name": "ShimmerSweep", "evidence": "光带扫过文字"}
    ]
  }'
```

#### 成功响应 (200)

```json
{
  "status": "success",
  "data": [
    {"name": "BlurReveal", "evidence": "文字从模糊到清晰"},
    {"name": "Typewriter", "evidence": "逐字出现效果"},
    {"name": "ShimmerSweep", "evidence": "光带扫过文字"}
  ]
}
```

#### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 400 | `任务类型为 xxx，仅 analyze-effect 可修改 effects` | task_id 对应的不是特效分析任务 |
| 400 | `任务状态为 xxx，仅 completed 可修改 effects` | 任务尚未完成或已失败 |

> 其余认证/权限错误与 `GET /task/{task_id}/stream` 一致。

### 14.3 GET /effects/demo/{filename} — 获取特效 Demo 视频

获取特效组件的预渲染演示视频。**公开访问，无需认证。**

| 属性 | 值 |
|---|---|
| **方法** | `GET` |
| **认证** | 不需要 |
| **响应类型** | `video/mp4` |

> **数据来源**：Demo 视频由 `effects-renderer` 项目预渲染生成，存放在 `backend/storage/effects/` 目录下。文件名采用特效名称的 kebab-case 形式（如 `typewriter.mp4`、`frosted-glass-wipe.mp4`）。前端通过 `GET /effects` 获取 `demo_path` 字段后拼接此 URL 即可访问。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `filename` | string | **是** | Demo 视频文件名（含 `.mp4` 扩展名），如 `typewriter.mp4` |

#### 请求示例

```bash
# 直接播放 Typewriter 特效的 Demo 视频
curl "http://127.0.0.1:8000/effects/demo/typewriter.mp4" -o demo.mp4
```

```html
<!-- 前端使用（Vite 代理会自动将 /api 前缀映射到后端） -->
<video src="/api/effects/demo/typewriter.mp4" controls></video>
```

#### 成功响应

直接返回 MP4 视频二进制流，`Content-Type` 为 `video/mp4`。

#### 错误响应

| HTTP 状态码 | detail | 说明 |
|---|---|---|
| 400 | `Invalid filename` | 文件名包含 `..`、`/` 或 `\` 等路径穿越字符 |
| 404 | `Demo not found` | 该特效暂无 Demo 视频（如 BlurReveal、TerminalSimulator、ChatToPreviewLayout） |

---

## 15. POST /plan — 生成视频模板

基于已完成的分析任务（/analyze-script、/analyze-visual 等），使用 LLM 将参考视频的叙事结构迁移到新的用户主题上，生成一个包含 segments 和 slots 的视频模板。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `script_task_id` | string | 否 | `null` | 已完成 script 分析的任务 ID |
| `visual_task_id` | string | 否 | `null` | 已完成 visual 分析的任务 ID |
| `audio_task_id` | string | 否 | `null` | 已完成 audio 分析的任务 ID |
| `effect_task_id` | string | 否 | `null` | 已完成 effect 分析的任务 ID |
| `user_brief` | string | **是** | — | 用户的新视频主题与需求描述 |
| `target_duration` | float | 否 | `null` | 目标视频时长（秒），不填则自动推算 |

> **约束**：`script_task_id` 和 `visual_task_id` 至少提供一个。

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "script_task_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "visual_task_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    "audio_task_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
    "user_brief": "做一个关于职场高效沟通的短视频，目标受众是刚入职的年轻人",
    "target_duration": 45.0
  }'
```

### 成功响应 (202)

模板生成任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"
  }
}
```

### 通过 SSE / 轮询获取模板

任务类型为 `"plan"`。`plan_id` 与 `task_id` 一致。任务完成后，`result` 字段直接包含完整的 `VideoTemplate` 结构：

```json
{
  "task_id": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii",
  "type": "plan",
  "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "created_at": "2026-06-08T12:00:00+00:00",
  "result": {
    "plan_id": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii",
    "created_at": "2026-06-08T12:00:05+00:00",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_brief": "做一个关于职场高效沟通的短视频",
    "reference_asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "estimated_duration": 45.0,
    "narrator_perspective": "second_person",
    "bgm_spec": {
      "genre": "pop", "bpm": 120.0, "mood": "energetic",
      "reference_audio_asset_id": "b2c3d4e5-...",
      "slot": { "slot_id": "bgm_main", "slot_type": "bgm", ... }
    },
    "segments": [
      {
        "index": 0, "stage": "hook", "start_time": 0.0, "end_time": 5.0,
        "narrative_intent": "...", "hook_type": "pain_point",
        "slots": [
          { "slot_id": "seg0_visual_text", "slot_type": "visual_text", ... },
          { "slot_id": "seg0_narration", "slot_type": "narration", ... },
          { "slot_id": "seg0_background_video", "slot_type": "background_video", ... }
        ]
      }
    ]
  }
}
```

> **与任务架构一致**：`plan_id == task_id`。前端通过 `GET /task/{task_id}/stream` (SSE) 即可获取完整模板，无需额外请求。字段说明同下方 PATCH 接口的模板结构。

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 400 | `任务 xxx 不存在` | 提供的 task_id 不在注册表中 |
| 400 | `任务 xxx 尚未完成，当前状态：running` | 参考的分析任务尚未完成 |
| 403 | `无权访问任务 xxx` | 参考任务不属于当前用户 |
| 422 | `script_task_id 和 visual_task_id 至少提供一个` | 请求体校验失败 |

---

## 16. PATCH /plan/{plan_id}/slot/{slot_id} — 填充模板槽位

为模板中的指定 slot 填充内容。支持三种方式：
- **user_upload**：上传已有的文件素材（需提供 asset_id），slot 状态变为 `filled`
- **ai_generate**：标记该 slot 待 AI 后续生成，slot 状态变为 `pending`
- **manual_input**：直接输入文本内容（适用于 visual_text / narration），slot 状态变为 `filled`

| 属性 | 值 |
|---|---|
| **方法** | `PATCH` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `plan_id` | string | **是** | 模板 ID（即任务 task_id，`plan_id == task_id`） |
| `slot_id` | string | **是** | 槽位 ID（如 `seg0_visual_text`、`bgm_main`） |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fill_method` | string | **是** | 填充方式：`user_upload` / `ai_generate` / `manual_input` |
| `value` | string | 条件必填 | `user_upload` 或 `manual_input` 时必填。`user_upload` 时为素材 asset_id；`manual_input` 时为文本内容 |

### 响应示例

**user_upload 填充成功：**

```bash
curl -X PATCH http://127.0.0.1:8000/plan/iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii/slot/seg0_background_video \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fill_method": "user_upload", "value": "c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1"}'
```

```json
{
  "status": "success",
  "data": {
    "slot_id": "seg0_background_video",
    "slot_type": "background_video",
    "description": "办公室场景的快速推进镜头",
    "constraints": { "duration_sec": 5.0, "camera_movement": "zoom_in" },
    "status": "filled",
    "fill_method": "user_upload",
    "value": "c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1"
  }
}
```

**ai_generate 标记待生成：**

```bash
curl -X PATCH http://127.0.0.1:8000/plan/iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii/slot/seg0_narration \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fill_method": "ai_generate"}'
```

```json
{
  "status": "success",
  "data": {
    "slot_id": "seg0_narration",
    "slot_type": "narration",
    "description": "用第二人称提问，语气带有疑惑感",
    "constraints": { "max_duration_sec": 5.0 },
    "status": "pending",
    "fill_method": "ai_generate",
    "value": null
  }
}
```

**manual_input 直接输入文本：**

```bash
curl -X PATCH http://127.0.0.1:8000/plan/iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii/slot/seg0_visual_text \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fill_method": "manual_input", "value": "为什么你的沟通总被无视？"}'
```

```json
{
  "status": "success",
  "data": {
    "slot_id": "seg0_visual_text",
    "slot_type": "visual_text",
    "description": "反问标题文字，点出沟通低效的痛点",
    "constraints": { "max_chars": 20, "position": "center", "appear_style": "typewriter" },
    "status": "filled",
    "fill_method": "manual_input",
    "value": "为什么你的沟通总被无视？"
  }
}
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 400 | `计划尚未生成完成` | plan 任务仍在运行中 |
| 403 | `无权访问该计划` | 模板不属于当前用户 |
| 403 | `无权使用该素材` | 提供的 asset_id 不属于当前用户 |
| 404 | `计划不存在` | plan_id 不存在（或对应任务类型非 plan） |
| 404 | `Slot xxx 不存在` | slot_id 在模板中不存在 |
| 404 | `素材 xxx 不存在` | 提供的 asset_id 无对应记录 |
| 422 | `fill_method 为 xxx 时必须提供 value` | 校验失败 |

---

## 17. POST /plan/{plan_id}/generate — 批量 AI 生成槽位内容

将模板中所有 `status="pending"` 的文本类槽位（visual_text / narration）一次性批量生成。LLM 会拥有全部 segment 的上下文，确保生成的文案在整条视频中叙事连贯、语气统一。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | —（无请求体） |

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `plan_id` | string | **是** | 模板 ID（即任务 task_id） |

### 成功响应 (202)

生成任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取结果。

```json
{
  "status": "success",
  "data": {
    "task_id": "kkkkkkkk-kkkk-kkkk-kkkk-kkkkkkkkkkkk"
  }
}
```

### 通过 SSE / 轮询获取结果

任务类型为 `"slot-generation"`，任务完成后 `result` 返回：

```json
{
  "generated_slots": [
    {"slot_id": "seg0_visual_text", "value": "为什么你的沟通总被无视？"},
    {"slot_id": "seg1_visual_text", "value": "原因很简单..."},
    {"slot_id": "seg0_narration", "value": "你有没有想过..."}
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `generated_slots` | array | 成功生成的槽位列表，每个元素包含 `slot_id` 和 `value` |
| `generated_slots[].slot_id` | string | 对应 slot 的唯一标识 |
| `generated_slots[].value` | string | LLM 生成的文本内容 |

> **提示**：前端可通过 `generated_slots.length` 获取生成数量。

若无 pending 槽位，返回 `{"generated_slots": []}`。

生成后的 slot 内容已直接写入原 plan 模板中。通过 `GET /task/{plan_id}/stream` 重新获取模板即可看到更新后的 slot 值（status 变为 `filled`，fill_method 变为 `ai_generate`）。

### 生成逻辑

1. 忽略已填（`filled`）和未标记（`empty`）的 slot，只处理 `status="pending"` 的 `visual_text` 和 `narration`
2. 若没有 pending 的文本 slot → 返回 `{"generated_slots": []}`
3. 将完整模板结构 + 用户 brief + 已填 slot 的值作为上下文传给 LLM
4. LLM 一次调用生成所有 pending slot 的文本内容
5. 写回模板，通过 `GET /task/{plan_id}/stream` 可获取更新后的模板

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 400 | `计划尚未生成完成` | plan 任务仍在运行中 |
| 403 | `无权访问该计划` | 模板不属于当前用户 |
| 404 | `计划不存在` | plan_id 不存在（或对应任务类型非 plan） |

---

## 18. POST /render — 渲染视频

基于已完成填充的 Plan 模板，调用 Remotion 引擎渲染生成最终的 MP4 视频。以异步任务模式运行，通过 SSE 实时推送渲染进度。

| 属性 | 值 |
|---|---|
| **方法** | `POST` |
| **认证** | 需要（Bearer Token） |
| **Content-Type** | `application/json` |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `plan_id` | string | **是** | 计划模板 ID（即 plan task_id，plan 任务必须已完成且 slot 已填充） |

> **前置条件**：
> 1. Plan 任务已完成（`POST /plan` 返回的 task_id，status 为 `completed`）
> 2. 所需 slot 已通过 `PATCH /plan/{plan_id}/slot/{slot_id}` 填充
> 3. BGM 已通过 `POST /analyze-audio` 生成（slot 中的 `reference_audio_asset_id` 指向有效的 BGM 音频文件）
>
> 渲染引擎使用 `viral-structure-engine/remotion-video` 项目，输出规格为 1080×1920（9:16 竖屏）30fps H.264 MP4。

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/render \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"}'
```

### 成功响应 (202)

渲染任务已提交，通过 `GET /task/{task_id}/stream` (SSE) 获取实时进度。

```json
{
  "status": "success",
  "data": {
    "task_id": "llllllll-llll-llll-llll-llllllllllll"
  }
}
```

### 通过 SSE / 轮询获取渲染进度

任务类型为 `"render"`。SSE 流式推送渲染各阶段进度：

**SSE 帧序列示例：**

```
data: {"phase":"loading","message":"Loading plan data..."}

data: {"phase":"bgm","message":"Loading BGM audio..."}

data: {"phase":"building","message":"Building render config..."}

data: {"phase":"rendering","progress":0,"frame":0,"totalFrames":498}

data: {"phase":"rendering","progress":12,"frame":60,"totalFrames":498}

data: {"phase":"rendering","progress":25,"frame":125,"totalFrames":498}

...

data: {"phase":"rendering","progress":100,"frame":498,"totalFrames":498}

data: {"phase":"saving","message":"Saving output video..."}

: keepalive

data: {"task_id":"llllllll-...","status":"completed","result":{...}}
```

**SSE 帧字段说明：**

| 帧类型 | phase 值 | 额外字段 | 说明 |
|---|---|---|---|
| 准备阶段 | `loading` | `message` | 读取 Plan 模板数据 |
| BGM 准备 | `bgm` | `message` | 拷贝 BGM 音频到渲染目录 |
| 构建配置 | `building` | `message` | 将 Plan 模板转换为 Remotion props JSON |
| 渲染中 | `rendering` | `progress`, `frame`, `totalFrames` | 逐帧渲染进度（百分比 + 当前帧/总帧数） |
| 保存中 | `saving` | `message` | 将输出 MP4 写入 storage，创建 Asset 记录 |

### 任务结果结构

任务完成后，`GET /task/{task_id}/stream` 返回的 `result` 字段：

```json
{
  "task_id": "llllllll-llll-llll-llll-llllllllllll",
  "type": "render",
  "resource_id": "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii",
  "status": "completed",
  "created_at": "2026-06-09T12:00:00+00:00",
  "result": {
    "asset_id": "m1m1m1m1-m1m1-m1m1-m1m1-m1m1m1m1m1m1",
    "path": "storage\\videos\\m1m1m1m1-....mp4",
    "duration": 45.0,
    "fps": 30,
    "width": 1080,
    "height": 1920
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `asset_id` | string | 渲染输出视频的 asset_id，可通过 `GET /files/{asset_id}` 下载/播放 |
| `path` | string | 视频文件的存储路径 |
| `duration` | float | 视频时长（秒） |
| `fps` | int | 帧率（固定 30fps） |
| `width` | int | 视频宽度（像素，固定 1080） |
| `height` | int | 视频高度（像素，固定 1920） |

### 渲染流程

```
① 读 PlanResult                   ← task_registry.get(plan_id).result
② 拷贝 BGM                        ← bgm_spec.reference_audio_asset_id → remotion-video/public/bgm.wav
③ 构建 remotion_props.json        ← PlanResult → scenes + beatFrames + textStyle
④ Remotion CLI 渲染               ← npx remotion.cmd render src/index.ts VideoComposition output.mp4 --props=...
⑤ 创建 Asset 记录                 ← Asset(asset_id, user_id, path, type="video")
⑥ 清理临时文件                    ← props JSON + 拷贝的 BGM
```

### 错误响应

| HTTP 状态码 | message | 说明 |
|---|---|---|
| 401 | `未提供认证令牌` | 请求头缺少 Authorization |
| 400 | `计划尚未生成完成，当前状态：running` | Plan 任务仍在运行中 |
| 403 | `无权访问该计划` | 模板不属于当前用户 |
| 404 | `计划 xxx 不存在` | plan_id 不在注册表中 |

**运行时错误**（通过 `GET /task/{task_id}/stream` 的 `status: "failed"` 和 `error` 字段返回）：

| 场景 | error 内容 |
|---|---|
| Plan 不存在或未完成 | `Plan not found or not completed` |
| Remotion 渲染失败 | `Remotion render failed with code {n}` |
| 输出文件丢失 | `Remotion 渲染后未找到输出文件` |
| 任务取消 | 清理临时文件后 `status: "cancelled"` |

---

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
| 400 | `缺少 asset_id 参数` | 压缩/分析时未提供 asset_id |
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

视频压缩 (`/compress`)、AI 分析 (`/analyze-script`、`/analyze-visual`、`/analyze-audio`、`/analyze-effect`)、视频切割 (`/split`)、模板生成 (`/plan`) 和视频渲染 (`/render`) 是长时异步操作。这些端点采用 **fire-and-forget** 模式：发起接口立即返回 `task_id`，客户端通过 **SSE 实时推送**获取进度和结果。

### 工作流程

```
POST /compress       → 202 { task_id }                    ← 立即返回
POST /analyze-script → 202 { task_id }                    ← 立即返回
POST /analyze-visual → 202 { task_id }                    ← 立即返回
POST /analyze-audio  → 202 { task_id }                    ← 立即返回
POST /analyze-effect → 202 { task_id }                    ← 立即返回
POST /split          → 202 { task_id }                    ← 立即返回
POST /plan           → 202 { task_id }                    ← 立即返回
POST /render          → 202 { task_id }                    ← 立即返回
                     → 连接 GET /task/{id}/stream (SSE)   ← 实时推送状态
                     ...（SSE 心跳保持连接）
                     → 最终帧 { task_id, status: "completed", result: {...} }
                     → 最终帧 { task_id, status: "failed", error: "..." }
POST /task/{id}/cancel → 200 "已发起取消"                   ← 中途取消
                     → 最终帧 { task_id, status: "cancelled" }
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
- **`/analyze-script` / `/analyze-visual` / `/analyze-effect`**: 底层异步 HTTP 请求的 TCP 连接被关闭，API 调用立即中止
- **`/analyze-audio`**: 底层 `ffmpeg` 和模型推理被 `asyncio.CancelledError` 中断，中间产物（storage/tmp 下的文件）由任务内部清理
- **`/split`**: 底层 `ffmpeg` 子进程被终止，已生成的临时切割文件被清理
- **`/plan`**: 底层异步 LLM 请求被 `asyncio.CancelledError` 中断，API 调用立即中止
- **`/render`**: 底层 Remotion CLI 子进程被终止，临时文件（props JSON + 拷贝的 BGM + 输出 MP4）被清理

### 注意事项

- 发起接口仅做参数校验（asset 是否存在、归属等），通过校验后立即返回 202
- 任务记录在服务内存中持久保存，服务重启后丢失
- 取消操作是尽力而为的——AI 模型可能已经消耗了部分 token
- **推荐使用 SSE**：`GET /task/{task_id}/stream` 提供实时推送，连接后立即获取当前状态，任务完成时自动推送结果，无需反复轮询
- 建议客户端通过 `GET /task/{task_id}/stream` (SSE) 订阅任务状态，无需轮询
