1. [x] `optim`: 使用 sse 代替轮询 (2026.06.05)
2. [x] `optim`: 优化鼠标拖动幕布速度 (2026.06.05)
3. [x] `feat`: 幕布拖拽数据保存 (2026.06.05)
4. [x] `optim`: cover image 截取选择 0.1s 而不是 1s (或是寻找一个最佳的 clip) (2026.06.06)
5. [ ] `feat`: 对于分析并选择特效, 可以给每一个 remotion 组件都生成一个简短的 fig, 然后让用户可以看到 AI 识别出来的特效都有什么.
6. [ ] `feat`: 并且提供一个搜索框, 可以让用户本地通过自然语言检索可能相关的特效 (通过设置一个 fuzzy search engine (lightweight) 版本)
7. [x] `feat`: 给 wire 添加箭头
8. [x] `feat`: 使用 driver.js 添加新手指引
9. [x] `feat`: 新手友好信息添加, 鼠标悬浮显示 tip note, 展示参数相关信息
10. [ ] `feat`: 动画化逐步跳出. 先只显示一个节点, 然后再得到行为后弹出后续节点. 以此来引导用户的注意力
11. [x] `feat`: 自定义布局, 允许用户保存自己喜欢的布局作为起始布局.
12. [x] `feat`: 定义 static 目录挂载, 同时限制用户只能访问自己上传或处理得到的素材
13. [x] `bug`: 当节点长度改变时, Wires 组件并没有自己更新
14. [x] `bug`: 当浏览器失去焦点时, @microsoft/fetch-event-source 疑似会自动重试, 从而导致反复请
求 /analyze-audio 接口, 重复实施某个任务. (2026.06.06)
15. [x] `bug`: 当有多个 NodeErrorToast 组件时, 一个组件的展开会导致其他组件一起被展开 (状态意外
共享)
16. [x] `bug`: /analyze-audio 因为 audio queue 没有放入 END_FLAG, 导致 queue 阻塞卡死. 
17. [ ] `feat`: Extracting Node 添加一个 TODO 列表 info. 
18. [x] `feat`: 修改 COMPRESS 节点按钮大小
19. [x] `feat`: 对于 visual analysis, 能够折叠所有 shots 以及 text elements
20. [ ] `optim`: 使用 hsl 颜色表示法来简化所有相关颜色的开发
21. [ ] `feat`: 添加双手指拖动移动幕布功能
22. [ ] `optim`: 对于音乐节点, 可以考虑使用 moving average, 或是下采样当样本数超过一定时
23. [x] `feat`: 我希望新添加一个 EffectAnalysis 节点, 其能够将视频按照 scene 切分 (2026.06.06)
24. [x] `feat`: 逐个 scene 分析其特效构成部分
25. [x] `feat`: 将 cover image 等添加一个 /files/{file_id} 链接. (让后端生成 cover image) (2026.06.06)
26. [x] `refac`: 重构 backend 代码, 使其符合 MVC 架构 (2026.06.07)
27. [x] `feat`: 可以框选多个节点一起移动
28. [x] `bug`: 没有保存 image asset (2026.06.08)
29. [ ] `feat`: 允许 analysis 单独重试
30. [x] `feat`: 优化 visual analysis 表达
31. [ ] `feat`: 允许 effects 中让用户自己添加 effect
32. [x] `feat`: 允许 slot 重新填写
33. [ ] `bug`: 当第一次上传失败后, 无法再次上传视频
34. [ ] `feat`: GenerateNode 节点没有 tour guide
35. [ ] `feat`: 左下角信息更新框选
36. [ ] `feat`: 被框选节点能够显示一个淡蓝色虚斜线 cover, 用于更清晰的标识被框选的节点