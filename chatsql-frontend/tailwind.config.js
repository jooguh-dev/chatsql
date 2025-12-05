/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // 将你原来的字体栈移到这里，作为默认 sans 字体
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"San Francisco"',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        // 代码字体，用于 SQL 编辑器
        mono: ['"SF Mono"', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        // Apple System Colors
        ios: {
          blue: '#007AFF',       // 主按钮、链接、激活状态
          gray: '#F5F5F7',       // 页面主背景
          surface: '#FFFFFF',    // 卡片、侧边栏背景
          text: '#1D1D1F',       // 主要文字
          subtext: '#86868B',    // 次要文字
          border: '#D2D2D7',     // 分割线
          destruct: '#FF3B30',   // 错误/删除 (Red)
          success: '#34C759',    // 成功 (Green)
        }
      },
      boxShadow: {
        // 极柔和的悬浮阴影，用于卡片
        'apple': '0 4px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        // 模态框或强调元素的阴影
        'apple-lg': '0 20px 40px rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '18px', // Apple 风格通常更圆润
      }
    },
  },
  plugins: [],
}