# S01 进入镜头 A/B 测试

## 生成目标

用同一张干净首帧分别生成豆包 Seedance 2.0 和 Runway Gen-4 Turbo 的 5 秒样片。只比较稳定推轨、几何一致性、通道安全和尾帧可续拍性。本轮不生成后续镜头。

首帧：`production/v5/source-frames/s01-entry-clean.png`

## 豆包 Seedance 2.0

设置：

- 模式：图生视频
- 模型：Seedance 2.0
- 时长：5 秒
- 比例：16:9
- 清晰度/质量：使用当前可选最高质量
- 音频：关闭；如果无法关闭，则要求只有克制的真实厂房环境声
- 参考图：只上传上述首帧，不再添加其他图片

提示词：

```text
以输入图片作为严格的第一帧和空间结构基准。摄影机沿中央完全畅通的黄色服务通道，进行缓慢、稳定、匀速的电影机推轨，五秒内只向前移动一小段，保持水平地平线、固定镜头高度和自然的广角透视。中央AGV以比摄影机稍慢的恒定低速向前行驶，始终保持在通道中央，不转向，不漂移。左侧安全围栏、六轴机械臂、封闭机床、右侧黑色显示器、吊顶桁架、天窗和管线必须保持原有位置、尺寸和结构；机械臂本镜头保持静止。自然天窗光线稳定，金属和地坪只有克制的真实反射。高端工业纪录片质感，真实摄影机惯性，轻微自然运动模糊。

不要新增或删除设备，不要复制物体，不要改变机械臂关节，不要让任何结构伸入通道，不要出现轨道、悬浮物、人员、字幕、标志、可读文字或水印。不要横摇、绕拍、变焦、滚转、抖动、突然加速、景深抽动、画面溶解或镜头切换。右侧显示器始终保持关闭的深色玻璃状态。
```

## Runway Gen-4 Turbo

设置：

- 模式：Image to Video
- 模型：Gen-4 Turbo
- 时长：5 秒
- 比例：16:9
- 参考图：使用同一张首帧
- 本轮最多生成 1 次，预算 25 credits

Prompt：

```text
The input image is the exact first frame and the locked spatial reference. A slow, perfectly stable, constant-speed cinematic dolly moves forward a short distance along the center of the completely unobstructed yellow service aisle. Keep the horizon level, camera height fixed, and wide-lens perspective unchanged. The AGV rolls forward slowly at a slightly lower speed than the camera, remaining centered in the aisle without turning or drifting. The fenced six-axis robot remains still. All safety fencing, enclosed machine tools, the dark inactive monitor on the right, roof trusses, skylights, pipes, floor markings, proportions, and clearances remain rigid and unchanged. Stable natural daylight, restrained realistic metal and floor reflections, premium industrial documentary cinematography, subtle physical camera inertia and natural motion blur. One continuous shot.

No new objects, no removed equipment, no duplicated parts, no geometry morphing, no aisle obstruction, no rails, no people, no readable text, no logos, no UI, no watermark. No pan, orbit, zoom, roll, shake, speed ramp, focus pumping, dissolve, or cut. The right monitor stays dark inactive glass for the entire shot.
```

## 导出与命名

下载平台导出的原始 MP4，不录屏、不剪辑、不转码：

- `S01_seedance2_5s_take01.mp4`
- `S01_runway_g4turbo_5s_take01.mp4`

将两个文件直接发回 Codex。先审核 S01，再从通过片段提取尾帧并编写 S02，避免无连续性地批量消耗额度。

## 直接淘汰条件

- AGV、机械臂或围栏变形、复制、穿模。
- 黄色通道被新结构遮挡。
- 摄影机横摇、绕拍、跳帧或突然加速。
- 右侧显示器出现乱码 UI。
- 出现平台水印或无法用于正式网站的 AI 标记。
- 尾帧已经模糊、畸变或不适合继续生成下一段。
