<script setup>
import { computed } from 'vue';
import { marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

marked.use(markedHighlight({
  langPrefix: 'hljs language-', 
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  }
}));

const props = defineProps({
  msg: { type: Object, required: true }
});

// 新增 'show-toast' 事件，用來呼叫 App.vue 的提示框
const emit = defineEmits(['copy-text', 'show-toast']);

// 1. 攔截 Markdown 渲染結果，偷偷塞入複製按鈕的 HTML
const renderedHtml = computed(() => {
  if (!props.msg.content) return '';
  let html = marked.parse(props.msg.content);
  
  // 使用正則表達式，把每個程式碼區塊包裝起來，並加上絕對定位的按鈕
  html = html.replace(
    /<pre><code/g, 
    '<div class="code-block-wrapper relative group my-4"><button class="copy-code-btn absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-xs text-gray-300 hover:text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-all z-10">複製代碼</button><pre><code'
  );
  html = html.replace(/<\/code><\/pre>/g, '</code></pre></div>');
  
  return html;
});

// 2. 事件委派：監聽整個 Markdown 區塊的點擊
const handleMarkdownClick = async (event) => {
  // 檢查被點擊的元素是不是我們剛剛塞進去的 'copy-code-btn'
  if (event.target.classList.contains('copy-code-btn')) {
    const btn = event.target;
    // 往上找到 wrapper，再往下找到 code 裡面的純文字
    const codeBlock = btn.closest('.code-block-wrapper').querySelector('code');
    
    if (codeBlock) {
      try {
        await navigator.clipboard.writeText(codeBlock.textContent);
        
        // 視覺回饋：把按鈕變成綠色打勾
        const originalText = btn.innerText;
        btn.innerText = '✅ 已複製';
        btn.classList.replace('bg-gray-700', 'bg-green-600');
        btn.classList.replace('text-gray-300', 'text-white');
        
        // 2秒後恢復原狀
        setTimeout(() => { 
          btn.innerText = originalText;
          btn.classList.replace('bg-green-600', 'bg-gray-700');
        }, 2000);
        
        emit('show-toast', '✅ 程式碼已複製！');
      } catch (err) {
        console.error('複製失敗', err);
      }
    }
  }
};

const handleCopyMessage = (text) => {
  emit('copy-text', text);
};
</script>

<template>
  <div class="mb-8 flex group" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
    <div v-if="msg.role === 'assistant'" class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold mr-3 shrink-0 mt-1">AI</div>

    <div class="max-w-[85%] relative">
      <div class="rounded-2xl p-5 shadow-sm" 
           :class="msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'">
        
        <p v-if="msg.role === 'user'" class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</p>
        
        <div v-else 
             @click="handleMarkdownClick"
             class="prose prose-sm md:prose-base prose-indigo max-w-none prose-pre:bg-[#0d1117] prose-pre:m-0 prose-pre:p-4"
             v-html="renderedHtml">
        </div>
      </div>

      <button v-if="msg.role === 'assistant'" 
              @click="handleCopyMessage(msg.content)"
              class="absolute -right-12 bottom-2 p-2 text-gray-400 hover:text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity"
              title="複製整段訊息">📋</button>
    </div>
  </div>
</template>

<style scoped>
/* 1. 取消 Tailwind Typography 預設幫 code 前後加的討厭引號 */
:deep(.prose :not(pre) > code::before),
:deep(.prose :not(pre) > code::after) {
  content: none !important;
}

/* 2. 針對「非區塊」的行內程式碼 (單反引號) 進行獨立樣式設定 */
:deep(.prose :not(pre) > code) {
  background-color: #f1f5f9; /* 淺灰藍色背景 (slate-100) */
  color: #e11d48;            /* 專業的代碼深粉紅色 (rose-600) */
  padding: 0.15rem 0.35rem;  /* 上下左右留白 */
  border-radius: 0.375rem;   /* 圓角 */
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; /* 等寬字體 */
  font-size: 0.875em;        /* 字體稍微縮小一點點會更精緻 */
  font-weight: 500;
  border: 1px solid #e2e8f0; /* 加一圈極細的邊框提升立體感 */
}
</style>