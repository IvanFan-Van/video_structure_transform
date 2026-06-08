/**
 * TypeScript 类型定义 — 与 Python transfer/schema.py 保持对应
 *
 * 所有类型定义遵循 remotion_props.json 的 schema 结构:
 *   RemotionProps → 顶层配置
 *   SceneData     → 单个场景渲染数据
 *   TextStyle     → 文字样式
 *   RemocnEffect  → remocn组件调用描述（支持递归嵌套）
 */

export interface TextStyle {
  fontSize: number;                              // 字体大小(px)
  color: string;                                 // 文字颜色(hex)
  fontWeight: string;                            // 字重: bold/normal/lighter
  animation: 'typewriter' | 'fade_in' | 'bounce' | 'slide_in' | 'glitch' | 'static';
  position_x: number;                            // 水平位置(0-100%)
  position_y: number;                            // 垂直位置(0-100%)
}

export interface RemocnEffect {
  component: string;                             // remocn组件名（必须在REMOCN_REGISTRY中注册）
  props: Record<string, unknown>;                // 组件props键值对
  children?: RemocnEffect[];                     // 子组件列表（容器型组件如SpringPopIn用）
}

export interface SceneData {
  id: string;                                    // 场景唯一标识（与slot label对应）
  slot_id: number;                               // 槽位序号
  startFrame: number;                            // 起始帧号
  durationFrames: number;                        // 持续帧数
  type: 'text_overlay' | 'emphasis_text' | 'product_centric' | 'curiosity_text' | 'remocn_composed';
  text: string;                                  // 渲染的文字内容
  textStyle: TextStyle;                          // 文字样式
  visualHint: string;                            // 画面描述线索
  emotion: string;                               // 情绪标签
  beatFrames: number[];                          // 该场景内的BGM卡点（相对帧号）
  hasMaterial: boolean;                          // 用户是否提供了视频/图片素材
  backgroundVideo: string | null;                // 背景视频文件名（已拷贝到public/）
  backgroundImage: string | null;                // 背景图片文件名（已拷贝到public/）
  backgroundColorFallback: string;               // 无素材时的纯色背景（hex）
  requiredElements: string[];                    // 关键视觉元素清单
  gapFilled: boolean;                            // 是否触发了素材缺口补全
  gapStrategy: string;                           // 补全策略描述
  fill_method: string;                           // 具体补全方式
  remocnEffects?: RemocnEffect[];                // remocn组件列表（仅type=remocn_composed时有效）
}

export interface RemotionProps {
  fps: number;                                   // 输出帧率（固定30）
  durationInFrames: number;                      // 总帧数
  width: number;                                 // 画面宽度(px)
  height: number;                                // 画面高度(px)
  scenes: SceneData[];                           // 场景列表（按startFrame排序）
  bgmPath: string;                               // BGM文件名
  voiceoverPath: string;                         // TTS旁白文件名
  voiceoverText: string;                         // TTS实际朗读文本
  rhythmPattern: string;                         // 节奏模式标签
  visualStyle: string;                           // 视觉风格标签
  gapReport: unknown[];                          // 缺口报告列表
  migrationSummary: unknown;                     // 迁移摘要
}
