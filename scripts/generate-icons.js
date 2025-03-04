const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');
const sharp = require('sharp');

// SVG数据
const svgContent = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="30%" stop-color="#2196F3" />
      <stop offset="90%" stop-color="#21CBF3" />
    </linearGradient>
  </defs>
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="url(#gradient)" opacity="0.2" />
  <path d="M7 7h2v10H7V7zm4 0h2v10h-2V7zm4 0h2v10h-2V7z" fill="url(#gradient)" />
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="url(#gradient)" />
  <circle cx="12" cy="12" r="1" fill="url(#gradient)" />
  <circle cx="8" cy="12" r="1" fill="url(#gradient)" />
  <circle cx="16" cy="12" r="1" fill="url(#gradient)" />
</svg>
`;

// 保存SVG文件
fs.writeFileSync(path.join(__dirname, '../frontend/public/logo.svg'), svgContent);

// 生成不同尺寸的PNG图标
const sizes = [16, 32, 48, 64, 128, 192, 512];

async function generateIcons() {
  try {
    // 生成各种尺寸的PNG
    for (const size of sizes) {
      await sharp(Buffer.from(svgContent))
        .resize(size, size)
        .png()
        .toFile(path.join(__dirname, `../frontend/public/logo${size}.png`));
    }

    // 特别生成favicon.ico（包含多个尺寸）
    await sharp(Buffer.from(svgContent))
      .resize(32, 32)
      .toFile(path.join(__dirname, '../frontend/public/favicon.ico'));

    console.log('图标生成成功！');
  } catch (error) {
    console.error('生成图标时出错：', error);
  }
}

generateIcons(); 