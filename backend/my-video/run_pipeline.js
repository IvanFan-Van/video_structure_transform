import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

// 确保核心文件夹存在
if (!fs.existsSync('video_slices')) fs.mkdirSync('video_slices');
if (!fs.existsSync('audio')) fs.mkdirSync('audio');

console.log('🚀 开始执行超级自动化视频管线 (Windows 优化版)...\n');

// ==========================================
// 1. 解析 narration.txt
// ==========================================
const txtPath = 'narration.txt';
if (!fs.existsSync(txtPath)) {
    console.error(`❌ 错误：找不到 ${txtPath} 文件，请先创建它。`);
    process.exit(1);
}

const content = fs.readFileSync(txtPath, 'utf8');
const parts = content.split(/\[(beat-\d+)\]/);
const pipelineConfig = [];

for (let i = 1; i < parts.length; i += 2) {
    const id = parts[i].trim();
    const text = parts[i + 1].trim().replace(/\s+/g, ' ');

    if (text) {
        pipelineConfig.push({
            id: id,
            text: text,
            // 使用 path.normalize 确保在 Windows 下输出正确的反斜杠路径
            html: path.normalize(`compositions/${id}.html`),
            audio: path.normalize(`audio/${id}.wav`)
        });
    }
}

console.log(`📝 成功解析文案！共检测到 ${pipelineConfig.length} 个 Beat 分镜。`);

// ==========================================
// 2. 核心管线循环：音频生成 + 视频渲染
// ==========================================
pipelineConfig.forEach((beat, index) => {
    console.log(`\n--------------------------------------------`);
    console.log(`🎬 [${index + 1}/${pipelineConfig.length}] 正在处理分镜: ${beat.id}`);
    console.log(`💬 对应文案: "${beat.text}"`);

    const cleanHtmlPath = beat.html;
    let actualHtml = cleanHtmlPath;

    // 智能匹配带有后缀的 HTML 文件
    if (!fs.existsSync(cleanHtmlPath)) {
        const dirFiles = fs.readdirSync('compositions');
        const matchedFile = dirFiles.find(f => f.startsWith(beat.id) && f.endsWith('.html'));
        if (matchedFile) {
            actualHtml = path.normalize(path.join('compositions', matchedFile));
        } else {
            console.error(`⚠️ 警告：找不到该 Beat 的 HTML 模版 (${cleanHtmlPath})，将跳过渲染。`);
            return;
        }
    }

    // A. 自动生成当前 Beat 的音频 (TTS)
    console.log(`🎙️  正在生成独立音频...`);
    const ttsCmd = `npx hyperframes tts --text "${beat.text}" -o "${beat.audio}"`;
    try {
        // 使用 inherit 暴露可能存在的音频生成错误
        execSync(ttsCmd, { stdio: 'inherit' });
        console.log(`   ↳ 音频处理完成。`);
    } catch (err) {
        console.error(`❌ 音频生成失败: ${beat.id}`);
        process.exit(1);
    }

    // B. 自动将 HTML 与刚生成的音频融合成单个视频切片
    console.log(`📹 正在渲染视频切片...`);
    const outputSlice = path.normalize(`video_slices/${beat.id}.mp4`);
    const renderCmd = `npx hyperframes render "${actualHtml}" --audio "${beat.audio}" --output "${outputSlice}"`;

    try {
        // 👇 核心修改：使用 inherit，如果失败，Puppeteer/Chrome 的报错会直接喷在屏幕上
        execSync(renderCmd, { stdio: 'inherit' });
        console.log(`   ↳ 视频渲染成功: ${outputSlice}`);
    } catch (err) {
        console.error(`❌ 视频渲染失败: ${beat.id}`);
        process.exit(1);
    }
});

// ==========================================
// 3. 终极无损拼接 (FFmpeg)
// ==========================================
console.log(`\n--------------------------------------------`);
console.log('🔗 所有分镜处理完毕，正在生成 FFmpeg 合并清单...');

const validBeats = pipelineConfig.filter(beat => fs.existsSync(path.normalize(`video_slices/${beat.id}.mp4`)));
const concatContent = validBeats.map(beat => `file 'video_slices/${beat.id}.mp4'`).join('\n');
fs.writeFileSync('concat_list.txt', concatContent);

console.log('🎬 正在合成为最终完整长视频...');
const finalOutput = 'index_final.mp4';
const concatCmd = `ffmpeg -f concat -safe 0 -i concat_list.txt -c copy -y ${finalOutput}`;

try {
    execSync(concatCmd, { stdio: 'inherit' });
    console.log(`\n🎉 🎉 🎉 奇迹时刻！全自动化视频完美诞生 -> ${finalOutput}`);
} catch (err) {
    console.error('❌ FFmpeg 合并失败，请确认系统是否安装了 ffmpeg 命令行工具。');
}