# migration_report.json 字段结构说明

> 供前端可视化 teammate 参考。每个字段的名称、类型、含义及完整示例。

`migration_report` 嵌入在 `remotion_props.json` 中，包含两份数据：
- `migrationSummary` — 迁移过程摘要
- `gapReport` — 素材缺口详情（数组）

---

## 1. MigrationSummary（迁移摘要）

| 字段 | 类型 | 含义 |
|------|------|------|
| `sourceVideo` | `string` | 源爆款视频文件名 |
| `theme` | `string` | 迁移后的新主题 |
| `slotsCount` | `number` | 场景槽位总数 |
| `gapsCount` | `number` | 素材缺口总数 |
| `filledGapsCount` | `number` | 已填充的缺口数 |
| `rhythmPattern` | `string` | 节奏模式（如 `steady_build`, `fast_start`, `peak_middle`） |
| `visualStyle` | `string` | 视觉风格（如 `subtitle_heavy`, `product_centric`, `person_led`, `mixed`） |

## 2. GapItem（缺口项 — 数组元素）

| 字段 | 类型 | 含义 |
|------|------|------|
| `slot_id` | `number` | 槽位序号（从 1 开始） |
| `label` | `string` | 槽位标签（如 `hook`, `cta`, `product_unboxing_show`） |
| `missing_type` | `string` | 缺失素材类型：`"video"` \| `"image"` \| `"voiceover"` \| `"text"` |
| `impact` | `string` | 影响等级：`"high"` \| `"medium"` \| `"low"` |
| `strategy` | `string` | LLM 推荐的补全策略描述 |
| `filled` | `boolean` | 是否已被管道自动补全 |
| `fill_method` | `string` | 补全方式：`"color_bg"` \| `"text_subtitle_only"` \| `""` (未补全) |

## 3. 完整示例

```json
{
  "migrationSummary": {
    "sourceVideo": "4.mp4",
    "theme": "儿童零食推荐--谢逸牌蛋糕",
    "slotsCount": 4,
    "gapsCount": 4,
    "filledGapsCount": 4,
    "rhythmPattern": "steady_build",
    "visualStyle": "product_centric"
  },
  "gapReport": [
    {
      "slot_id": 1,
      "label": "social_proof_hook",
      "missing_type": "video",
      "impact": "high",
      "strategy": "找不到足够产品展示素材时，使用3D渲染生成产品多角度展示环，配合镜头每1秒切换一个展示角度的节奏",
      "filled": true,
      "fill_method": "color_bg"
    },
    {
      "slot_id": 2,
      "label": "product_unboxing_show",
      "missing_type": "video",
      "impact": "high",
      "strategy": "缺少真实开箱素材时使用特写镜头拍摄撕开包装的素材拼接，加上飘散粒子等视觉化效果强化感知",
      "filled": true,
      "fill_method": "color_bg"
    },
    {
      "slot_id": 3,
      "label": "taste_experience_display",
      "missing_type": "video",
      "impact": "high",
      "strategy": "无法拍摄吃播素材时可拍摄特写镜头展示产品被掰开或撕开的细腻口感，加上咬痕模拟特效强化感知",
      "filled": true,
      "fill_method": "color_bg"
    },
    {
      "slot_id": 4,
      "label": "platform_official_outro",
      "missing_type": "image",
      "impact": "medium",
      "strategy": "无官方片尾素材时直接生成大色块背景加平台规范信息排版的静态图片替代",
      "filled": true,
      "fill_method": "color_bg"
    }
  ]
}
```

## 4. 前端可视化建议

### 4.1 概要卡片

用 `migrationSummary` 渲染顶部概览卡：

```
┌──────────────────────────────────────────┐
│  源视频: 4.mp4     节奏: steady_build    │
│  主题: 儿童零食推荐  视觉: product_centric │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  场景: 4   缺口: 4  已补全: 4  ✅        │
└──────────────────────────────────────────┘
```

### 4.2 缺口列表

`gapReport[]` 按 `impact` 排序后渲染为列表，每条显示：

| 槽位 | 缺失类型 | 影响 | 补全策略 | 状态 |
|------|----------|------|----------|------|
| social_proof_hook | video | 🔴 high | 用3D渲染生成... | ✅ color_bg |
| product_unboxing_show | video | 🔴 high | 拍摄撕开包装素材... | ✅ color_bg |
| taste_experience_display | video | 🔴 high | 拍摄特写镜头展示... | ✅ color_bg |
| platform_official_outro | image | 🟡 medium | 大色块背景+平台信息 | ✅ color_bg |

### 4.3 状态图标映射

| `impact` | 图标 | 颜色 |
|----------|------|------|
| `high` | 🔴 | `#FF4444` |
| `medium` | 🟡 | `#FFAA00` |
| `low` | 🟢 | `#44AA44` |

| `filled` | 显示 |
|----------|------|
| `true` | ✅ + fill_method |
| `false` | ❌ 未补全 (#FF4444 高亮) |

### 4.4 时间线可视化

以 `slot_id` 为横轴、`impact` 为纵轴渲染缺口时间线，缺口位置用红色标记，已补全的用绿色标记。横轴下方用 `fill_method` 文字标注每段的补全方式。

---

*文档版本: 2026-06-07 · 配合 `remotion_props.json` 同步更新*
