/**
 * Remotion 渲染入口 — 注册 Root 组件
 *
 * 这是 Remotion CLI 渲染命令的入口文件，通过 registerRoot() 注册 Root 组件。
 * 执行渲染时: npx remotion render src/index.ts VideoComposition out/demo.mp4 --props=props.json
 */
import { registerRoot } from 'remotion';
import { Root } from './Root';
registerRoot(Root);
