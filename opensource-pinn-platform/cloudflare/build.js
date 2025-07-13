#!/usr/bin/env node

/**
 * Cloudflare Workers Build Script
 * Prepares the Workers deployment without Python dependencies
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 Building Cloudflare Workers deployment...');

// Ensure we're only deploying JavaScript/HTML files
const srcDir = path.join(__dirname, 'src');
const distDir = path.join(__dirname, 'dist');

// Create dist directory
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}

// Copy JavaScript files
function copyJSFiles(src, dest) {
    const items = fs.readdirSync(src);
    
    for (const item of items) {
        const srcPath = path.join(src, item);
        const destPath = path.join(dest, item);
        
        if (fs.statSync(srcPath).isDirectory()) {
            if (!fs.existsSync(destPath)) {
                fs.mkdirSync(destPath, { recursive: true });
            }
            copyJSFiles(srcPath, destPath);
        } else if (item.endsWith('.js') || item.endsWith('.html') || item.endsWith('.css')) {
            fs.copyFileSync(srcPath, destPath);
            console.log(`✅ Copied: ${item}`);
        }
    }
}

copyJSFiles(srcDir, distDir);

console.log('✨ Build complete! Ready for Cloudflare Workers deployment.');
console.log('📦 Files prepared in ./dist/');
console.log('🌐 Deploy with: wrangler deploy');