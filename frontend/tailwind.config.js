// 檔案路徑：frontend/tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // 設定思源黑體為預設的 sans 字體，霞鶩文楷為 serif
        sans: ['"Noto Sans TC"', 'sans-serif'],
        serif: ['"LXGW WenKai TC"', 'serif'],
      }
    },
  },
  plugins: [
    // 等一下會安裝這個官方插件，專門用來美化 Markdown 排版
    require('@tailwindcss/typography'),
  ],
}