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

const emit = defineEmits(['copy-text', 'show-toast']);

// ==========================================
// 【新增】解析使用者訊息 (處理 JSON 與多模態陣列)
// ==========================================
const parsedUserContent = computed(() => {
  if (props.msg.role !== 'user') return { text: '', images: [], files: [] };

  let content = props.msg.content;

  // 1. 如果是從資料庫撈出來的 JSON 字串，先轉回物件/陣列
  if (typeof content === 'string') {
    try {
      if (content.trim().startsWith('[')) {
        content = JSON.parse(content);
      }
    } catch (e) {
      // 解析失敗代表它是普通純文字，不需處理
    }
  }

  let text = '';
  let images = [];
  let files = []; 

  // 2. 如果是陣列 (多模態格式)，分類取出文字、圖片與文件
  if (Array.isArray(content)) {
    content.forEach(item => {
      if (item.type === 'text') {
        text += item.text + '\n';
      } else if (item.type === 'image_url') {
        const url = item.image_url.url;
        if (url.startsWith('data:image/')) {
          images.push(url); // 收集圖片 Base64
        } else if (url.startsWith('data:application/pdf')) {
          files.push('📄 PDF 文件'); // 收集 PDF 標籤
        }
      }
    });
  } else {
    // 3. 純文字
    text = content;
  }

  return { text: text.trim(), images, files };
});

// ==========================================
// 保留原有的 AI Markdown 渲染與複製功能
// ==========================================
const renderedHtml = computed(() => {
  if (!props.msg.content || props.msg.role !== 'assistant') return '';
  let html = marked.parse(props.msg.content);
  
  html = html.replace(
    /<pre><code/g, 
    '<div class="code-block-wrapper relative group my-4"><button class="copy-code-btn absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-xs text-gray-300 hover:text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-all z-10">複製代碼</button><pre><code'
  );
  html = html.replace(/<\/code><\/pre>/g, '</code></pre></div>');
  
  return html;
});

const handleMarkdownClick = async (event) => {
  if (event.target.classList.contains('copy-code-btn')) {
    const btn = event.target;
    const codeBlock = btn.closest('.code-block-wrapper').querySelector('code');
    
    if (codeBlock) {
      try {
        await navigator.clipboard.writeText(codeBlock.textContent);
        const originalText = btn.innerText;
        btn.innerText = '✅ 已複製';
        btn.classList.replace('bg-gray-700', 'bg-green-600');
        btn.classList.replace('text-gray-300', 'text-white');
        
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
        
        <div v-if="msg.role === 'user'" class="flex flex-col gap-3">
          <div v-if="parsedUserContent.images.length > 0" class="flex flex-wrap gap-2">
            <img v-for="(img, idx) in parsedUserContent.images" :key="idx" 
                :src="img" 
                class="max-w-full h-auto max-h-48 rounded-lg object-cover border border-white/20 shadow-sm" />
          </div>
          
          <div v-if="parsedUserContent.files.length > 0" class="flex flex-wrap gap-2">
            <span v-for="(file, idx) in parsedUserContent.files" :key="idx"
                  class="bg-indigo-500 text-indigo-100 text-xs px-2 py-1 rounded border border-indigo-400 font-medium tracking-wide">
              {{ file }}
            </span>
          </div>

          <p v-if="parsedUserContent.text" class="whitespace-pre-wrap leading-relaxed">{{ parsedUserContent.text }}</p>
        </div>
        
        
        <div v-else 
             @click="handleMarkdownClick"
             class="prose prose-sm md:prose-base prose-indigo max-w-none prose-pre:bg-[#0d1117] prose-pre:m-0 prose-pre:p-4"
             v-html="renderedHtml">
        </div>

        <div v-if="msg.role === 'assistant' && msg.total_tokens" 
            class="mt-4 border-t border-gray-100 pt-3 flex flex-col gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
          
          <div class="flex justify-end items-center gap-2 text-[10px] font-mono text-gray-400">
            <span class="bg-gray-50 px-2 py-0.5 rounded border border-gray-100">
              📥 In: {{ msg.prompt_tokens }}
            </span>
            <span class="bg-gray-50 px-2 py-0.5 rounded border border-gray-100">
              📤 Out: {{ msg.total_tokens - msg.prompt_tokens }}
            </span>
          </div>

          <div class="flex justify-end items-center gap-2 text-[11px] font-mono">
            <span class="bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full border border-indigo-100 font-bold">
              ⚡ Total: {{ msg.total_tokens }}
            </span>
            <span v-if="msg.cost > 0" class="bg-green-50 text-green-600 px-2 py-0.5 rounded-full border border-green-100 font-bold">
              💰 ${{ msg.cost.toFixed(5) }}
            </span>
          </div>
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
/* 你的樣式完美保留 */
:deep(.prose :not(pre) > code::before),
:deep(.prose :not(pre) > code::after) {
  content: none !important;
}

:deep(.prose :not(pre) > code) {
  background-color: #f1f5f9; 
  color: #e11d48;            
  padding: 0.15rem 0.35rem;  
  border-radius: 0.375rem;   
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; 
  font-size: 0.875em;        
  font-weight: 500;
  border: 1px solid #e2e8f0; 
}
</style>