<script setup>
import { ref, watch, nextTick, computed, onMounted } from 'vue';
import ChatBubble from './components/ChatBubble.vue';
import ChatInput from './components/ChatInput.vue';

// === 1. 定義狀態 (State) ===
const model = ref('gemini/gemini-2.5-flash');
const temperature = ref(0.7);
const messages = ref([]);
const isGenerating = ref(false);

// UI 狀態
const isRightPanelOpen = ref(true); // 控制右側面板收合
const chatContainer = ref(null);    // 用於自動捲動的參考點
const isLeftPanelOpen = ref(true); // 控制左側選單開關
const conversations = ref([]);     // 存放歷史對話列表
const currentConversationId = ref(null); // 目前正在看的對話 ID

// 提示詞模板功能
const promptTemplates = [
  { name: '預設助手', prompt: '你是一個得力的 AI 助手，請用繁體中文回答。' },
  { name: '資深工程師', prompt: '你是一位資深軟體工程師。請提供結構化、高效的程式碼，並在程式碼區塊外簡要說明原理。' },
  { name: '精準翻譯官', prompt: '你是一位專業翻譯。請將我輸入的內容翻譯成流暢、通順的繁體中文，無需額外解釋。' }
];
const systemPrompt = ref(promptTemplates[0].prompt);

// 取得所有歷史對話列表
const fetchConversations = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/conversations');
    conversations.value = await res.json();
  } catch (error) {
    showToast('❌ 無法載入歷史對話');
  }
};

// 建立新對話
const createNewChat = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/conversations', { method: 'POST' });
    const data = await res.json();
    currentConversationId.value = data.id;
    messages.value = []; // 清空畫面上的對話
    await fetchConversations(); // 更新左側列表
  } catch (error) {
    showToast('❌ 無法建立新對話');
  }
};

// 載入特定對話歷史
const loadConversation = async (id) => {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/conversations/${id}`);
    const data = await res.json();
    currentConversationId.value = data.id;
    messages.value = data.messages; // 把後端記憶塞回畫面
    nextTick(() => scrollToBottom());
  } catch (error) {
    showToast('❌ 無法載入對話內容');
  }
};

// 網頁剛開啓時的初始化動作
onMounted(async () => {
  await fetchConversations();
  if (conversations.value.length > 0) {
    await loadConversation(conversations.value[0].id); // 載入最新的一筆
  } else {
    await createNewChat(); // 沒半筆就創一筆新的
  }
});


// === 2. 功能函數 ===

// 自動捲動到底部
const scrollToBottom = async () => {
  await nextTick(); // 等待 Vue 重新渲染 DOM
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

// 監聽 messages 變化，有新訊息時觸發捲動
watch(messages, () => {
  scrollToBottom();
}, { deep: true });

// === 新增 Toast 提示狀態 ===
const toastMessage = ref('');
let toastTimeout = null;

const showToast = (msg) => {
  toastMessage.value = msg;
  // 如果已經有計時器，先清除掉，避免連續點擊時提早消失
  if (toastTimeout) clearTimeout(toastTimeout);
  // 設定 2.5 秒後自動消失
  toastTimeout = setTimeout(() => {
    toastMessage.value = '';
  }, 2500);
};

// === 修改原本的複製功能 ===
const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showToast('✅ 訊息已複製到剪貼簿！'); // 替換掉原本的 alert
  } catch (err) {
    console.error('複製失敗:', err);
    showToast('❌ 複製失敗，請手動選取複製');
  }
};

// 發送訊息與接收串流
const sendMessage = async (text) => {
  // 防呆：如果正在生成中就阻擋
  if (isGenerating.value) return;

  // 使用子組件傳上來的 text
  messages.value.push({ role: 'user', content: text });
  isGenerating.value = true;

  messages.value.push({ role: 'assistant', content: '' });
  const currentAssistantIndex = messages.value.length - 1;

  try {
    const recentHistory = messages.value.slice(0, -1).slice(-6);
    const apiMessages = [
      { role: 'system', content: systemPrompt.value },
      ...recentHistory
    ];

    const response = await fetch('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model.value,
        messages: apiMessages,
        temperature: temperature.value,
        conversation_id: currentConversationId.value
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunkText = decoder.decode(value, { stream: true });
      messages.value[currentAssistantIndex].content += chunkText;
      scrollToBottom();
    }

  } catch (error) {
    messages.value[currentAssistantIndex].content += '\n\n**[系統提示]**：發生錯誤，請檢查後端連線。';
  } finally {
    isGenerating.value = false;
  }
};
</script>

<template>
  <div class="flex h-screen w-full bg-[#F9FAFB] text-gray-800 font-sans relative overflow-hidden">

    <transition name="toast">
      <div v-if="toastMessage" 
           class="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 bg-gray-800 text-white px-5 py-2.5 rounded-full shadow-lg text-sm font-medium tracking-wide flex items-center gap-2">
        {{ toastMessage }}
      </div>
    </transition>

    <div :class="isLeftPanelOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full overflow-hidden border-none p-0'" 
         class="bg-gray-900 text-gray-300 flex flex-col transition-all duration-300 ease-in-out shrink-0 z-20">
      
      <div class="p-4 w-64 flex-shrink-0 flex flex-col h-full">
        
        <button @click="createNewChat" 
                class="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-white py-2.5 rounded-lg border border-gray-700 transition-colors mb-4 shadow-sm font-medium">
          <span>+</span> 新對話
        </button>

        <div class="text-xs font-semibold text-gray-500 mb-2 px-1 uppercase tracking-wider">歷史紀錄</div>

        <div class="flex-1 overflow-y-auto space-y-1 pr-1">
          <button v-for="conv in conversations" :key="conv.id"
                  @click="loadConversation(conv.id)"
                  :class="conv.id === currentConversationId ? 'bg-indigo-600 text-white shadow-md' : 'hover:bg-gray-800 hover:text-white'"
                  class="w-full text-left px-3 py-2.5 rounded-md text-sm truncate transition-colors">
            {{ conv.title }}
          </button>
        </div>
      </div>
    </div>


    <div class="flex-1 flex flex-col relative transition-all duration-300 min-w-0">
      
      <div class="h-14 shrink-0 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10">
        
        <div class="flex items-center gap-3">
          <button @click="isLeftPanelOpen = !isLeftPanelOpen" class="p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-800 rounded-md transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
          </button>
          <h1 class="text-lg font-bold text-gray-800 tracking-wide">My AI Workspace</h1>
        </div>

        <button @click="isRightPanelOpen = !isRightPanelOpen" 
                class="p-2 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors">
          <span v-if="isRightPanelOpen">關閉設定 ▶</span>
          <span v-else>◀ 開啟設定</span>
        </button>
      </div>

      <div ref="chatContainer" class="flex-1 min-h-0 overflow-y-auto p-4 md:p-8 scroll-smooth">
        <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400">
          <p class="text-xl font-medium mb-2">今天想聊些什麼？</p>
          <p class="text-sm">請在下方輸入訊息開始對話，或在右側調整模型與提示詞。</p>
        </div>

        <ChatBubble 
          v-for="(msg, index) in messages" 
          :key="index" 
          :msg="msg" 
          @copy-text="copyMessage" 
          @show-toast="showToast" 
        />
      </div>

      <ChatInput 
        class="shrink-0"
        :isGenerating="isGenerating" 
        @send="sendMessage" 
      />
    </div>


    <div :class="isRightPanelOpen ? 'w-80 translate-x-0' : 'w-0 translate-x-full overflow-hidden border-none p-0'" 
         class="bg-white border-l border-gray-200 flex flex-col transition-all duration-300 ease-in-out shrink-0">
      
      <div class="p-6 flex flex-col gap-6 h-full overflow-y-auto w-80">
        <h2 class="text-lg font-bold text-gray-800 border-b pb-2">參數設定</h2>
        
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">模型 (Model)</label>
          <select v-model="model" class="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50">
            <option value="gemini/gemini-2.5-flash">Gemini 2.5 Flash</option>
            <option value="openai/gpt-5-chat-latest">OpenAI GPT-5-chat</option>
            <option value="groq/llama-3.1-8b-instant">Groq Llama-3.1 8B</option>
          </select>
        </div>

        <div class="p-4 bg-gray-50 rounded-lg border border-gray-100">
          <div class="flex justify-between mb-2">
            <label class="text-sm font-semibold text-gray-700">創造力 (Temperature)</label>
            <span class="text-sm font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{{ temperature }}</span>
          </div>
          <input type="range" v-model.number="temperature" min="0" max="2" step="0.1" class="w-full accent-indigo-600">
          <p class="text-xs text-gray-500 mt-2">數值越高回答越發散，數值越低越精準。</p>
        </div>

        <div class="flex-1 flex flex-col">
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-semibold text-gray-700">系統提示詞 (System Prompt)</label>
          </div>
          
          <div class="flex flex-wrap gap-2 mb-3">
            <button v-for="tpl in promptTemplates" :key="tpl.name" 
                    @click="systemPrompt = tpl.prompt"
                    class="text-xs px-2.5 py-1 rounded-full border border-gray-300 hover:border-indigo-500 hover:text-indigo-600 transition-colors bg-white">
              {{ tpl.name }}
            </button>
          </div>

          <textarea 
            v-model="systemPrompt" 
            class="w-full flex-1 border border-gray-300 rounded-lg p-3 resize-none focus:ring-2 focus:ring-indigo-500 outline-none text-sm text-gray-700 bg-gray-50 leading-relaxed"
            placeholder="設定 AI 的角色與行為...">
          </textarea>
        </div>
      </div>
    </div>
    
  </div>
</template>

<style>
/* 自訂捲動軸樣式，讓畫面更精緻 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
/* Toast 提示框的過場動畫 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px); /* 讓它有一點往下掉出現的感覺 */
}
</style>