# 自测文档 (Self-Testing Guide)

本文档描述了如何对 `backend` 的各个 API 端点进行功能验证与 Edge Case 测试。所有示例默认 `Base URL = http://127.0.0.1:8000`。

---

## 目录

- [自测文档 (Self-Testing Guide)](#自测文档-self-testing-guide)
  - [目录](#目录)
    - [0. 前置准备](#0-前置准备)
    - [1. 认证 (Auth)](#1-认证-auth)
    - [2. 文件上传 (Upload)](#2-文件上传-upload)
    - [3. 异步任务通用机制](#3-异步任务通用机制)
    - [4. 视频压缩 (Compress)](#4-视频压缩-compress)
    - [5. 叙事结构分析 (Analyze Script)](#5-叙事结构分析-analyze-script)
    - [6. 视频视觉层分析 (Analyze Visual)](#6-视频视觉层分析-analyze-visual)
    - [7. 音频分析 (Analyze Audio)](#7-音频分析-analyze-audio)
    - [8. 视频切割 (Split)](#8-视频切割-split)
    - [9. 特效分析 (Analyze Effect)](#9-特效分析-analyze-effect)
    - [10. 特效库查询与校正 (Effects)](#10-特效库查询与校正-effects)
    - [11. 特效 Demo 视频 (Demo)](#11-特效-demo-视频-demo)
    - [12. Plan 模板系统](#12-plan-模板系统)
    - [13. 视频渲染 (Render)](#13-视频渲染-render)
    - [14. 文件访问 (Files)](#14-文件访问-files)
    - [15. 全流程端到端测试](#15-全流程端到端测试)
    - [附录 A: 环境变量预设脚本](#附录-a-环境变量预设脚本)
    - [附录 B: 快速断言速查](#附录-b-快速断言速查)

---

### 0. 前置准备

#### 0.1 启动后端

```bash
cd backend
uv run python -m app.main
```

确认服务正常运行：

```bash
curl -s http://127.0.0.1:8000/
# 预期: {"status":"success","data":"ok"}
```

#### 0.2 准备测试视频

准备一个 10-30 秒的 MP4 视频文件，复制到项目根目录：

```bash
# 示例：使用 ffmpeg 生成一个 15 秒测试视频
ffmpeg -f lavfi -i testsrc=duration=15:size=1080x1920:rate=30 \
       -f lavfi -i sine=frequency=440:duration=15 \
       -c:v libx264 -pix_fmt yuv420p -c:a aac \
       -shortest test.mp4
```

**⚠️ 重要提示**：部分 LLM 分析接口（`/analyze-script`, `/analyze-visual`, `/analyze-effect`）会消耗 API Token。建议准备一个简短的测试视频以降低费用。

#### 0.3 辅助变量

```bash
BASE="http://127.0.0.1:8000"
TEST_VIDEO="./test.mp4"
TEST_IMAGE=""  # 可选，如有测试图片可填入路径
```

---

### 1. 认证 (Auth)

#### 1.1 正常注册

```bash
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}' | python -m json.tool
```

**预期**：HTTP 201，返回 `user_id` 和 `email`。

#### 1.2 重复注册

```bash
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
```

**预期**：HTTP 400，`message` 包含 "已注册"。

#### 1.3 注册 — 空字段

```bash
# 缺少 email
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"password":"test123456"}'
# 预期: 400, "邮箱不能为空"

# 缺少 password
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com"}'
# 预期: 400, "密码不能为空"
```

#### 1.4 正常登录

```bash
# 保存 token 到环境变量
TOKEN=$(curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

echo "TOKEN=$TOKEN"
```

**预期**：HTTP 200，返回 `access_token`、`token_type`、`expires_at`、`user`。

#### 1.5 登录 — 错误密码

```bash
curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrongpassword"}'
# 预期: 401, "密码错误"
```

#### 1.6 登录 — 未注册邮箱

```bash
curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"noexist@example.com","password":"anything"}'
# 预期: 404, "未注册"
```

#### 1.7 认证拦截 — 缺少 Token

```bash
curl -s $BASE/effects
# 预期: 401, "未提供认证令牌"
```

#### 1.8 认证拦截 — 无效 Token

```bash
curl -s $BASE/effects -H "Authorization: Bearer invalid_token_here"
# 预期: 401, "令牌已过期或无效"
```

#### 1.9 Token 过期测试（可选，需改环境变量）

将 `ACCESS_TOKEN_EXPIRE_MINUTES=0.02`（约 1 秒）后重新启动，登录后等待 2 秒再调用：

```bash
curl -s $BASE/effects -H "Authorization: Bearer $TOKEN"
# 预期: 401
```

---

### 2. 文件上传 (Upload)

#### 2.1 上传视频

```bash
UPLOAD_RES=$(curl -s -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_VIDEO")
echo "$UPLOAD_RES" | python -m json.tool
ASSET_ID=$(echo "$UPLOAD_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['asset_id'])")
COVER_ID=$(echo "$UPLOAD_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['cover_image_asset_id'])")
echo "ASSET_ID=$ASSET_ID"
echo "COVER_ID=$COVER_ID"
```

**预期**：HTTP 201，`type` 为 `"video"`，包含 `metadata`（`width`, `height`, `fps`, `duration` 等）和 `cover_image_asset_id`。

#### 2.2 上传图片（可选）

```bash
# 如有测试图片
curl -s -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.png"
# 预期: 201, type="image", 无 cover_image_asset_id
```

#### 2.3 上传不支持的文件类型

```bash
echo "hello" > /tmp/test.txt
curl -s -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.txt"
# 预期: 400, "不支持的文件类型"
rm /tmp/test.txt
```

#### 2.4 上传 — 无认证

```bash
curl -s -X POST $BASE/upload -F "file=@$TEST_VIDEO"
# 预期: 401
```

---

### 3. 异步任务通用机制

> 以下模式适用于所有返回 `202` + `task_id` 的端点：`/compress`, `/analyze-script`, `/analyze-visual`, `/analyze-audio`, `/analyze-effect`, `/split`, `/plan`, `/plan/{plan_id}/generate`, `/render`。

#### 3.1 轮询 — 任务运行中 → 完成

```bash
# 先启动一个异步任务拿到 TASK_ID
# 以 compress 为例
COMPRESS_RES=$(curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
TASK_ID=$(echo "$COMPRESS_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "TASK_ID=$TASK_ID"

# 轮询等待完成
sleep 2
curl -s $BASE/task/$TASK_ID -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**预期**：若任务完成则 `status: "completed"` 且包含 `result` 字段；若仍在运行则 `status: "running"`。

#### 3.2 SSE 实时推送 — 推荐方式

```bash
# Bash 下监听 SSE 流（--no-buffer 确保实时输出）
TASK_ID="<从异步请求中获取>"
curl -N --no-buffer $BASE/task/$TASK_ID/stream \
  -H "Authorization: Bearer $TOKEN"
# 预期: 逐行输出 SSE 事件，最终事件包含 result
```

**预期行为**：
- 连接时若任务已完成 → 推送 1 条完整 `to_dict()` 后关闭
- 连接时若任务运行中 → 推送 `{"task_id":"...","status":"running"}`，每 15s keepalive，完成后推送最终状态并关闭

#### 3.3 查询不存在的任务

```bash
curl -s $BASE/task/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN"
# 预期: 404, "任务 xxx 不存在"
```

#### 3.4 以其他用户查询任务

```bash
# 先注册另一个用户
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"other@example.com","password":"other123"}'
TOKEN2=$(curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"other@example.com","password":"other123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 用 TOKEN2 查询 TOKEN 创建的任务
curl -s $BASE/task/$TASK_ID -H "Authorization: Bearer $TOKEN2"
# 预期: 403, "无权访问该任务"
```

#### 3.5 取消任务

启动一个耗时较长的任务（如使用 LLM 的 `/analyze-script`），然后立即取消：

```bash
TASK_ID="<从异步请求中获取>"
curl -s -X POST $BASE/task/$TASK_ID/cancel \
  -H "Authorization: Bearer $TOKEN"
# 预期: 200, "已发起取消"

# 验证取消状态
curl -s $BASE/task/$TASK_ID -H "Authorization: Bearer $TOKEN"
# 预期: status: "cancelled"
```

#### 3.6 取消已完成的/不存在的/他人的任务

```bash
# 取消已完成的任务
curl -s -X POST $BASE/task/$TASK_ID/cancel -H "Authorization: Bearer $TOKEN"
# 预期: 404（已完成的任务在 registry 中以 status="completed" 存留，取消接口对已完成无影响）
# 实际行为取决于实现，记录响应

# 取消不存在的任务
curl -s -X POST $BASE/task/00000000-0000-0000-0000-000000000000/cancel \
  -H "Authorization: Bearer $TOKEN"
# 预期: 404

# 取消他人的任务
curl -s -X POST $BASE/task/$TASK_ID/cancel -H "Authorization: Bearer $TOKEN2"
# 预期: 403
```

---

### 4. 视频压缩 (Compress)

#### 4.1 默认压缩

```bash
COMPRESS_RES=$(curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
COMPRESS_TASK_ID=$(echo "$COMPRESS_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "COMPRESS_TASK_ID=$COMPRESS_TASK_ID"
```

**预期**：HTTP 202，返回 `task_id`。

等待完成后查询结果：

```bash
# 等待任务完成
sleep 5
COMPRESS_STATUS=$(curl -s $BASE/task/$COMPRESS_TASK_ID -H "Authorization: Bearer $TOKEN")
echo "$COMPRESS_STATUS" | python -m json.tool
# 确认 status="completed"，result.asset_id 有值
COMPRESSED_ASSET_ID=$(echo "$COMPRESS_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['result']['asset_id'])")
echo "COMPRESSED_ASSET_ID=$COMPRESSED_ASSET_ID"
```

**预期 result 字段**：`asset_id`, `source_asset_id`, `type: "video"`, `path`, `metadata`, `cover_image_asset_id`。

#### 4.2 自定义压缩参数

```bash
curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "'$ASSET_ID'",
    "vcodec": "libx264",
    "crf": 28,
    "scale_width": 720,
    "max_fps": 24,
    "target_a_bitrate": "128k"
  }'
# 预期: 202
```

#### 4.3 固定码率模式

```bash
curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "'$ASSET_ID'",
    "target_v_bitrate": "2M",
    "max_fps": 30
  }'
# 预期: 202
```

#### 4.4 Edge Cases

```bash
# 缺少 asset_id
curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
# 预期: 400, "缺少 asset_id 参数"

# 不存在的 asset_id
curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"00000000-0000-0000-0000-000000000000"}'
# 预期: 404, "素材 xxx 不存在"

# 无权访问的素材 (用 TOKEN2)
curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}"
# 预期: 403
```

---

### 5. 叙事结构分析 (Analyze Script)

#### 5.1 正常流程

```bash
SCRIPT_RES=$(curl -s -X POST $BASE/analyze-script \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
SCRIPT_TASK_ID=$(echo "$SCRIPT_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "SCRIPT_TASK_ID=$SCRIPT_TASK_ID"

# SSE 流式等待
curl -N --no-buffer $BASE/task/$SCRIPT_TASK_ID/stream \
  -H "Authorization: Bearer $TOKEN"
```

**预期 result 字段**：`narrator_perspective`, `stages`（含 6 个阶段：`hook`, `setup`, `story`, `insight`, `cta`, `outro`）。

验证 stages 中每个阶段的字段：`visual_text`, `audio_text`, `start_time`, `end_time`, `emotional_tone`，以及 `hook` 阶段的 `hook_type`、`cta` 阶段的 `cta_type`。

#### 5.2 Edge Cases

```bash
# 缺少 asset_id
curl -s -X POST $BASE/analyze-script \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
# 预期: 400

# 素材不存在
curl -s -X POST $BASE/analyze-script \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"00000000-0000-0000-0000-000000000000"}'
# 预期: 404

# 无权访问
curl -s -X POST $BASE/analyze-script \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}"
# 预期: 403
```

---

### 6. 视频视觉层分析 (Analyze Visual)

#### 6.1 正常流程

```bash
VISUAL_RES=$(curl -s -X POST $BASE/analyze-visual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
VISUAL_TASK_ID=$(echo "$VISUAL_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "VISUAL_TASK_ID=$VISUAL_TASK_ID"
```

**预期 result 字段**：`total_duration`, `pacing`（`avg_shot_duration`, `pacing_category`, `acceleration_points`）, `shots[]`, `transitions[]`, `text_elements[]`, `text_density_curve[]`。

#### 6.2 Edge Cases

```bash
# 文件过大（超过 MAX_ANALYZE_SIZE_MB 限制）
# 先用一个很大的视频文件测试
curl -s -X POST $BASE/analyze-visual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}"
# 若文件 > MAX_ANALYZE_SIZE_MB: 400, 提示压缩
# 若文件 <= 限制: 202

# 缺少 asset_id: 400
# 素材不存在: 404
# 无权访问: 403
# 测试方法同上
```

---

### 7. 音频分析 (Analyze Audio)

#### 7.1 正常流程

```bash
AUDIO_RES=$(curl -s -X POST $BASE/analyze-audio \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
AUDIO_TASK_ID=$(echo "$AUDIO_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "AUDIO_TASK_ID=$AUDIO_TASK_ID"

# 等待完成
sleep 10
AUDIO_STATUS=$(curl -s $BASE/task/$AUDIO_TASK_ID -H "Authorization: Bearer $TOKEN")
echo "$AUDIO_STATUS" | python -m json.tool
```

**预期 result 字段**：`audio_asset_id`, `bgm_path`, `duration`, `genre`, `bpm`, `beat_timings[]`, `energy_curve[]`, `spectral_centroid[]`, `onset_envelope[]`, `dynamic_range`。

> **注意**：音频分析较耗时（需提取音轨 + 人声分离 + librosa 分析），建议等待 30-60 秒。

#### 7.2 Edge Cases

```bash
# 图片 asset_id（不支持）
# 先上传一张图片获取 IMG_ASSET_ID
# curl ... analyze-audio -d "{\"asset_id\":\"$IMG_ASSET_ID\"}"
# 预期: 400, "不支持的文件类型"

# 缺少 asset_id: 400
# 素材不存在: 404
# 无权访问: 403
```

---

### 8. 视频切割 (Split)

#### 8.1 默认切割 (scenedetect)

```bash
SPLIT_RES=$(curl -s -X POST $BASE/split \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
SPLIT_TASK_ID=$(echo "$SPLIT_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "SPLIT_TASK_ID=$SPLIT_TASK_ID"
```

**预期 result 字段**：`source_asset_id`, `method: "scenedetect"`, `total_segments`, `segments[]`（含 `index`, `start_sec`, `end_sec`, `duration`, `cut_score`），`clip_assets[]`（含 `asset_id`, `index`, `path`, `metadata`）。

#### 8.2 AI 语义切割

```bash
SPLIT_AI_RES=$(curl -s -X POST $BASE/split \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"'$ASSET_ID'","use_ai":true}')
# 预期: 202
# method="ai", segments[] 含 reason 字段而非 cut_score
```

#### 8.3 自定义 scenedetect 参数

```bash
curl -s -X POST $BASE/split \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"'$ASSET_ID'","threshold":20.0,"min_scene_len":30}'
# 预期: 202
```

#### 8.4 Edge Cases

```bash
# 缺少 asset_id: 400
# 素材不存在: 404
# 无权访问: 403
# 源文件丢失: 500 (需手动删除 storage 中的源文件来模拟)
```

---

### 9. 特效分析 (Analyze Effect)

#### 9.1 正常流程

```bash
EFFECT_RES=$(curl -s -X POST $BASE/analyze-effect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}")
EFFECT_TASK_ID=$(echo "$EFFECT_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "EFFECT_TASK_ID=$EFFECT_TASK_ID"
```

**预期 result 字段**：`observations`（自由文本），`effects[]`（数组，每项含 `name` + `evidence`）。

#### 9.2 Edge Cases

```bash
# 文件过大
# 测试方法同 analyze-script

# 缺少 asset_id: 400
# 素材不存在: 404
# 无权访问: 403
```

---

### 10. 特效库查询与校正 (Effects)

#### 10.1 查询全量特效库

```bash
curl -s $BASE/effects -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**预期**：返回 58 条特效记录，每条含 `name`, `category`, `description`, `demo_path`。

**验证 demo_path**：

```bash
curl -s $BASE/effects -H "Authorization: Bearer $TOKEN" \
  | python -c "
import sys, json
data = json.load(sys.stdin)['data']
with_demo = [e['name'] for e in data if e['demo_path']]
without_demo = [e['name'] for e in data if e['demo_path'] is None]
print(f'With demo: {len(with_demo)}')
print(f'Without demo: {len(without_demo)}')
print('Without demo:', without_demo)
"
```

**预期**：55 条有 `demo_path`，3 条为 `null`（`BlurReveal`, `TerminalSimulator`, `ChatToPreviewLayout`）。

#### 10.2 模糊搜索

```bash
# 按 name 搜索
curl -s "$BASE/effects?q=blur" -H "Authorization: Bearer $TOKEN"
# 预期: 包含 BlurReveal, FrostedGlassWipe, BrushStrokeSimulator 等含 "blur" 的记录

# 按 category 搜索
curl -s "$BASE/effects?q=typography" -H "Authorization: Bearer $TOKEN"
# 预期: 返回 Typography 分类下的所有记录

# 按 description 搜索
curl -s "$BASE/effects?q=模糊" -H "Authorization: Bearer $TOKEN"
# 预期: 返回 description 中包含 "模糊" 的记录

# 空搜索 (无 q 参数)
curl -s "$BASE/effects" -H "Authorization: Bearer $TOKEN"
# 预期: 返回全部 58 条

# 无匹配结果
curl -s "$BASE/effects?q=xyznonexistent123" -H "Authorization: Bearer $TOKEN"
# 预期: 200, data=[]

# 无认证
curl -s "$BASE/effects"
# 预期: 401
```

#### 10.3 PATCH — 校正任务特效

```bash
# 前提：先完成一个 analyze-effect 任务，拿到 EFFECT_TASK_ID

# 正常校正
curl -s -X PATCH $BASE/effects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "'$EFFECT_TASK_ID'",
    "effects": [
      {"name": "Typewriter", "evidence": "逐字出现"},
      {"name": "SpringPopIn", "evidence": "弹性弹出"}
    ]
  }' | python -m json.tool
# 预期: 200, data 返回替换后的 effects 列表
```

#### 10.4 PATCH — Edge Cases

```bash
# 对非 analyze-effect 类型的任务进行校正
curl -s -X PATCH $BASE/effects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"$COMPRESS_TASK_ID\",\"effects\":[]}"
# 预期: 400, "任务类型为 compress，仅 analyze-effect 可修改 effects"

# 对未完成的任务进行校正
# (需要先启动一个 analyze-effect 任务，趁它还在 running 时调用)
# 预期: 400, "任务状态为 running，仅 completed 可修改 effects"

# 不存在的 task_id
curl -s -X PATCH $BASE/effects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"00000000-0000-0000-0000-000000000000","effects":[]}'
# 预期: 404
```

---

### 11. 特效 Demo 视频 (Demo)

#### 11.1 正常获取 Demo 视频

```bash
# 下载 typewriter 特效的 demo
curl -s -o /tmp/demo_typewriter.mp4 \
  -w "HTTP %{http_code}, Size: %{size_download} bytes, Content-Type: %{content_type}" \
  $BASE/effects/demo/typewriter.mp4
# 预期: 200, Content-Type: video/mp4, 文件可正常播放
```

```bash
# 验证更多 demo
curl -s -o /tmp/demo_spring.mp4 \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/effects/demo/spring-pop-in.mp4

curl -s -o /tmp/demo_matrix.mp4 \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/effects/demo/matrix-decode.mp4
```

#### 11.2 无 Demo 的特效

```bash
# BlurReveal 没有对应的 demo 文件
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  $BASE/effects/demo/blur-reveal.mp4
# 预期: 404

curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  $BASE/effects/demo/terminal-simulator.mp4
# 预期: 404

curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  $BASE/effects/demo/chat-to-preview-layout.mp4
# 预期: 404
```

#### 11.3 路径穿越防护

```bash
# 尝试读取上级目录文件
curl -s $BASE/effects/demo/../../../etc/passwd
# 预期: 400, "Invalid filename"

# 尝试读取绝对路径
curl -s $BASE/effects/demo/C:/Windows/System32/drivers/etc/hosts
# 预期: 400, "Invalid filename"

# 带反斜杠的路径
curl -s $BASE/effects/demo/..\\..\\test.txt
# 预期: 400, "Invalid filename"

# 不存在的文件名（正常格式但文件不存在）
curl -s $BASE/effects/demo/nonexistent.mp4
# 预期: 404, "Demo not found"
```

#### 11.4 公开访问验证

```bash
# 无需 Token 即可访问
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  $BASE/effects/demo/typewriter.mp4
# 预期: 200（无需 Authorization header）

# 传了 Token 也可访问（向后兼容）
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  $BASE/effects/demo/typewriter.mp4 \
  -H "Authorization: Bearer $TOKEN"
# 预期: 200
```

#### 11.5 前端 URL 链路验证

```bash
# 模拟前端实际使用的 URL（Vite 代理会将 /api 前缀剥离）
# 在开发环境下，前端访问 /api/effects/demo/typewriter.mp4
# Vite 会代理到 http://127.0.0.1:8000/effects/demo/typewriter.mp4

# 验证 demo_path 字段拼接：
# 前端拿到 demo_path="/effects/demo/typewriter.mp4"
# 拼接为 "/api/effects/demo/typewriter.mp4"
# Vite 剥离 "/api" → "/effects/demo/typewriter.mp4"
```

---

### 12. Plan 模板系统

#### 12.1 正常生成 Plan

```bash
# 前提：已完成 script 和 visual 分析任务
PLAN_RES=$(curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_task_id": "'$SCRIPT_TASK_ID'",
    "visual_task_id": "'$VISUAL_TASK_ID'",
    "audio_task_id": "'$AUDIO_TASK_ID'",
    "effect_task_id": "'$EFFECT_TASK_ID'",
    "user_brief": "做一个关于职场高效沟通的短视频，目标受众是刚入职的年轻人",
    "target_duration": 45.0
  }')
PLAN_ID=$(echo "$PLAN_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "PLAN_ID=$PLAN_ID"
# 预期: 202
```

**等待完成后的 result 字段**：`plan_id`, `user_brief`, `reference_asset_id`, `estimated_duration`, `narrator_perspective`, `bgm_spec`, `segments[]`（每个 segment 含 `stage`, `start_time`, `end_time`, `narrative_intent`, `slots[]`）。

#### 12.2 Plan — Edge Cases

```bash
# 缺少 script_task_id 和 visual_task_id（至少提供一个）
curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_brief":"测试"}'
# 预期: 422

# 传入未完成的任务
curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"script_task_id\":\"<一个 running 中的 task_id>\",\"user_brief\":\"测试\"}"
# 预期: 400

# 传入不存在的 task_id
curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_task_id":"00000000-0000-0000-0000-000000000000","user_brief":"测试"}'
# 预期: 400

# 无权访问他人的任务
curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"script_task_id\":\"$SCRIPT_TASK_ID\",\"user_brief\":\"测试\"}"
# 预期: 403
```

#### 12.3 填充 Slot — user_upload

```bash
# 先用 plan 的 slots 列表找一个 slot_id
# 例如 seg0_background_video
SLOT_ID="seg0_background_video"  # 替换为实际的 slot_id

curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"fill_method\":\"user_upload\",\"value\":\"$ASSET_ID\"}" | python -m json.tool
# 预期: 200, slot status="filled", fill_method="user_upload"
```

#### 12.4 填充 Slot — ai_generate

```bash
# 标记为待 AI 生成
SLOT_ID="seg0_narration"  # 替换为实际的 slot_id

curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"ai_generate"}' | python -m json.tool
# 预期: 200, slot status="pending", fill_method="ai_generate"
```

#### 12.5 填充 Slot — manual_input

```bash
SLOT_ID="seg0_visual_text"  # 替换为实际的 slot_id

curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"manual_input","value":"为什么你的沟通总被无视？"}' | python -m json.tool
# 预期: 200, slot status="filled", fill_method="manual_input"
```

#### 12.6 Slot — Edge Cases

```bash
# 不存在的 plan_id
curl -s -X PATCH $BASE/plan/00000000-0000-0000-0000-000000000000/slot/any \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"manual_input","value":"test"}'
# 预期: 404, "计划不存在"

# 不存在的 slot_id
curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/nonexistent_slot \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"manual_input","value":"test"}'
# 预期: 404, "Slot xxx 不存在"

# user_upload 缺少 value
curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"user_upload"}'
# 预期: 422

# manual_input 缺少 value
curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"manual_input"}'
# 预期: 422

# 无效的 fill_method
curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"invalid_method","value":"test"}'
# 预期: 422

# 无权访问他人的 plan
curl -s -X PATCH $BASE/plan/$PLAN_ID/slot/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"fill_method":"manual_input","value":"test"}'
# 预期: 403

# 计划尚未生成完成
# (需在 plan 任务 running 状态时测试)
# 预期: 400, "计划尚未生成完成"
```

#### 12.7 批量 AI 生成 Slot 内容

```bash
GEN_RES=$(curl -s -X POST $BASE/plan/$PLAN_ID/generate \
  -H "Authorization: Bearer $TOKEN")
GEN_TASK_ID=$(echo "$GEN_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "GEN_TASK_ID=$GEN_TASK_ID"
# 预期: 202
```

**完成后 result**：`{"generated": N}`（N 为生成的 slot 数量）。

#### 12.8 Generate — Edge Cases

```bash
# 无 pending slot 时生成
# 将所有 slot 填满后再次调用 generate
# 预期: 202, 完成后 result={"generated":0}

# 计划不存在
curl -s -X POST $BASE/plan/00000000-0000-0000-0000-000000000000/generate \
  -H "Authorization: Bearer $TOKEN"
# 预期: 404

# 无权访问
curl -s -X POST $BASE/plan/$PLAN_ID/generate \
  -H "Authorization: Bearer $TOKEN2"
# 预期: 403
```

---

### 13. 视频渲染 (Render)

#### 13.1 前置条件检查

渲染前需要：
1. Plan 已完成
2. 所需 slot 已填充（至少 visual_text + background_video 等核心 slot）
3. BGM 已就绪

#### 13.2 正常渲染

```bash
RENDER_RES=$(curl -s -X POST $BASE/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"plan_id\":\"$PLAN_ID\"}")
RENDER_TASK_ID=$(echo "$RENDER_RES" | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "RENDER_TASK_ID=$RENDER_TASK_ID"

# SSE 实时进度
curl -N --no-buffer $BASE/task/$RENDER_TASK_ID/stream \
  -H "Authorization: Bearer $TOKEN"
```

**SSE 进度帧预期**：
- `{"phase":"loading","message":"Loading plan data..."}`
- `{"phase":"bgm","message":"Loading BGM audio..."}`
- `{"phase":"building","message":"Building render config..."}`
- `{"phase":"rendering","progress":N,"frame":N,"totalFrames":N}`
- `{"phase":"saving","message":"Saving output video..."}`
- 最终：`{"status":"completed","result":{...}}`

**result 字段**：`asset_id`, `path`, `duration`, `fps`, `width`, `height`。

#### 13.3 Render — Edge Cases

```bash
# 计划未完成 (传入一个 running 状态的 plan_id)
# 预期: 400, "计划尚未生成完成，当前状态：running"

# 计划不存在
curl -s -X POST $BASE/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"00000000-0000-0000-0000-000000000000"}'
# 预期: 404

# 无权访问
curl -s -X POST $BASE/render \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"plan_id\":\"$PLAN_ID\"}"
# 预期: 403
```

---

### 14. 文件访问 (Files)

#### 14.1 正常访问素材文件

```bash
# 访问上传的视频
curl -s -o /tmp/video.mp4 \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/files/$ASSET_ID -H "Authorization: Bearer $TOKEN"
# 预期: 200, 文件成功下载

# 访问封面图
curl -s -o /tmp/cover.png \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/files/$COVER_ID -H "Authorization: Bearer $TOKEN"
# 预期: 200

# 访问压缩后的视频
curl -s -o /tmp/compressed.mp4 \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/files/$COMPRESSED_ASSET_ID -H "Authorization: Bearer $TOKEN"
# 预期: 200 (压缩后的文件应比原始文件小)

# 访问 BGM 音频
BGM_ASSET_ID=$(echo "$AUDIO_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['result']['audio_asset_id'])")
curl -s -o /tmp/bgm.wav \
  -w "HTTP %{http_code}, Size: %{size_download} bytes\n" \
  $BASE/files/$BGM_ASSET_ID -H "Authorization: Bearer $TOKEN"
# 预期: 200
```

#### 14.2 Edge Cases

```bash
# 无认证
curl -s $BASE/files/$ASSET_ID
# 预期: 401

# 不存在的 asset_id
curl -s $BASE/files/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN"
# 预期: 404, "文件不存在"

# 无权访问
curl -s $BASE/files/$ASSET_ID -H "Authorization: Bearer $TOKEN2"
# 预期: 403, "无权访问该文件"

# Token 格式错误
curl -s $BASE/files/$ASSET_ID \
  -H "Authorization: Bearer"
# 预期: 401
```

---

### 15. 全流程端到端测试

以下是一步一步的完整测试链路，建议按顺序执行并在每步记录结果。

```bash
# ===== Phase 1: 认证 =====
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"e2e123456"}' | python -m json.tool

TOKEN=$(curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"e2e123456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
echo "Phase 1 OK: TOKEN acquired"

# ===== Phase 2: 上传视频 =====
UPLOAD=$(curl -s -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_VIDEO")
ASSET_ID=$(echo "$UPLOAD" | python -c "import sys,json; print(json.load(sys.stdin)['data']['asset_id'])")
echo "Phase 2 OK: ASSET_ID=$ASSET_ID"

# ===== Phase 3: 压缩视频 =====
COMPRESS_TASK=$(echo $(curl -s -X POST $BASE/compress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
# 等待完成...
sleep 5
echo "Phase 3 OK: compress completed"

# ===== Phase 4: 叙事分析 =====
SCRIPT_TASK=$(echo $(curl -s -X POST $BASE/analyze-script \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 4 OK: SCRIPT_TASK_ID=$SCRIPT_TASK (wait for completion)"

# ===== Phase 5: 视觉分析 =====
VISUAL_TASK=$(echo $(curl -s -X POST $BASE/analyze-visual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 5 OK: VISUAL_TASK_ID=$VISUAL_TASK (wait for completion)"

# ===== Phase 6: 音频分析 =====
AUDIO_TASK=$(echo $(curl -s -X POST $BASE/analyze-audio \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 6 OK: AUDIO_TASK_ID=$AUDIO_TASK (wait for completion)"

# ===== Phase 7: 视频切割 =====
SPLIT_TASK=$(echo $(curl -s -X POST $BASE/split \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 7 OK: SPLIT_TASK_ID=$SPLIT_TASK (wait for completion)"

# ===== Phase 8: 特效分析 =====
EFFECT_TASK=$(echo $(curl -s -X POST $BASE/analyze-effect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 8 OK: EFFECT_TASK_ID=$EFFECT_TASK (wait for completion)"

# ===== Phase 9: 查询特效库 =====
curl -s $BASE/effects -H "Authorization: Bearer $TOKEN" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'Phase 9 OK: {len(d[\"data\"])} effects')"

# ===== Phase 10: 校正特效（PATCH） =====
curl -s -X PATCH $BASE/effects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"$EFFECT_TASK\",\"effects\":[]}"
echo "Phase 10 OK: effects corrected"

# ===== Phase 11: 生成 Plan =====
# (确保 Phase 4,5,6,8 已完成)
PLAN_TASK=$(echo $(curl -s -X POST $BASE/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"script_task_id\":\"$SCRIPT_TASK\",
    \"visual_task_id\":\"$VISUAL_TASK\",
    \"audio_task_id\":\"$AUDIO_TASK\",
    \"effect_task_id\":\"$EFFECT_TASK\",
    \"user_brief\":\"做一个关于职场高效沟通的短视频\",
    \"target_duration\": 30.0
  }") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 11 OK: PLAN_ID=$PLAN_TASK (wait for completion)"

# ===== Phase 12: 填充 Slot =====
# (根据 plan 的实际 slot 填补，此处为示例)
# ... PATCH 各个 slot ...

# ===== Phase 13: 批量生成 =====
GEN_TASK=$(echo $(curl -s -X POST $BASE/plan/$PLAN_TASK/generate \
  -H "Authorization: Bearer $TOKEN") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 13 OK: GEN_TASK_ID=$GEN_TASK"

# ===== Phase 14: 渲染 =====
RENDER_TASK=$(echo $(curl -s -X POST $BASE/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"plan_id\":\"$PLAN_TASK\"}") | python -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
echo "Phase 14 OK: RENDER_TASK_ID=$RENDER_TASK (wait for completion)"

# ===== Phase 15: 下载渲染结果 =====
RENDER_RESULT=$(curl -s $BASE/task/$RENDER_TASK -H "Authorization: Bearer $TOKEN")
RENDER_ASSET_ID=$(echo "$RENDER_RESULT" | python -c "import sys,json; print(json.load(sys.stdin)['data']['result']['asset_id'])")
curl -s -o /tmp/final_output.mp4 \
  $BASE/files/$RENDER_ASSET_ID -H "Authorization: Bearer $TOKEN"
echo "Phase 15 OK: final video downloaded"
```

> **注意**：每步的异步任务（Phase 4-8, 11, 13, 14）需要等待其完成后才能进入下一步。建议在各 Phase 之间插入轮询检查逻辑。

---

### 附录 A: 环境变量预设脚本

将以下内容保存为 `self_test_env.sh`，在每个测试会话开始时执行：

```bash
#!/bin/bash
BASE="http://127.0.0.1:8000"
TEST_VIDEO="./test.mp4"

# 生成测试视频（如不存在）
if [ ! -f "$TEST_VIDEO" ]; then
  ffmpeg -f lavfi -i testsrc=duration=15:size=1080x1920:rate=30 \
         -f lavfi -i sine=frequency=440:duration=15 \
         -c:v libx264 -pix_fmt yuv420p -c:a aac \
         -shortest "$TEST_VIDEO"
fi

# 注册 + 登录
curl -s -X POST $BASE/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}' > /dev/null 2>&1

TOKEN=$(curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 上传视频
UPLOAD=$(curl -s -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_VIDEO")
ASSET_ID=$(echo "$UPLOAD" | python -c "import sys,json; print(json.load(sys.stdin)['data']['asset_id'])")
COVER_ID=$(echo "$UPLOAD" | python -c "import sys,json; print(json.load(sys.stdin)['data']['cover_image_asset_id'])")

echo "=== Environment Ready ==="
echo "BASE=$BASE"
echo "TOKEN=$TOKEN"
echo "ASSET_ID=$ASSET_ID"
echo "COVER_ID=$COVER_ID"
echo "TEST_VIDEO=$TEST_VIDEO"
```

---

### 附录 B: 快速断言速查

| 测试项 | curl 命令片段 | 预期 HTTP |
|--------|-------------|----------|
| 健康检查 | `curl $BASE/` | 200 |
| 注册-空 email | `-d '{"password":"x"}'` | 400 |
| 登录-错误密码 | `-d '{"email":"x","password":"wrong"}'` | 401 |
| 上传-无认证 | `-F "file=@test.mp4"` | 401 |
| 上传-非视频 | `-F "file=@test.txt"` | 400 |
| GET /effects 无认证 | `curl $BASE/effects` | 401 |
| GET /effects 搜索 | `?q=typewriter` | 200 |
| GET /demo 正常 | `/effects/demo/typewriter.mp4` | 200 |
| GET /demo 路径穿越 | `/effects/demo/../../../etc/passwd` | 400 |
| GET /demo 不存在 | `/effects/demo/nonexist.mp4` | 404 |
| PATCH /effects 非effect任务 | `task_id=<compress_task>` | 400 |
| PATCH /effects 未完成 | `task_id=<running_task>` | 400 |
| GET /task 不存在 | `00000000-...` | 404 |
| GET /task 无权 | 用 TOKEN2 查询 TOKEN 的任务 | 403 |
| GET /files 无认证 | 不带 Authorization | 401 |
| GET /files 不存在 | `00000000-...` | 404 |
| GET /files 无权 | 用 TOKEN2 查询 TOKEN 的文件 | 403 |
| POST /compress 无 asset_id | `-d '{}'` | 400 |
| POST /plan 无 brief | `-d '{"script_task_id":"..."}'` | 422 |
| PATCH slot 不存在 | `plan/.../slot/nonexist` | 404 |
| POST /render plan未完成 | 传入 running 的 plan_id | 400 |
