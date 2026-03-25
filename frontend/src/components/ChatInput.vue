<script setup>
import { ref, computed } from 'vue';
import PromptLibraryModal from './PromptLibraryModal.vue';

// 接收 App.vue 傳來的狀態
const props = defineProps({
  isGenerating: { type: Boolean, default: false },
  supportsImage: { type: Boolean, default: false },
  supportsPdf: { type: Boolean, default: false }
});

// 新增 'show-toast' 事件來觸發警告
const emit = defineEmits(['send', 'show-toast']);

const userInput = ref('');
const fileInput = ref(null);
const attachedFiles = ref([]); // 新增：存放準備上傳的檔案 (Base64)
const isPromptModalOpen = ref(false); // 控制彈窗開關

// 動態計算可以選擇的檔案類型
const acceptedFileTypes = computed(() => {
  let types = [];
  if (props.supportsImage) types.push('image/*');
  if (props.supportsPdf) types.push('.pdf');
  return types.join(',');
});

// 點擊迴紋針按鈕
const triggerFileSelect = () => {
  if (!props.supportsImage && !props.supportsPdf) {
    emit('show-toast', '⚠️ 目前選擇的模型不支援任何檔案上傳喔！');
    return;
  }
  fileInput.value.click();
};

// 處理檔案選擇 (轉成 Base64 以供預覽與傳送)
const handleFileChange = (event) => {
  const files = event.target.files;
  if (!files.length) return;

  const file = files[0];

  // 🛡️ 【防呆機制】：檢查檔案類型與模型能力是否匹配
  if (file.type === 'application/pdf' && !props.supportsPdf) {
    emit('show-toast', '⚠️ 目前的模型 (如 GPT-5) 不支援直接上傳 PDF 喔！');
    event.target.value = ''; // 清空選擇
    return;
  }
  if (file.type.startsWith('image/') && !props.supportsImage) {
    emit('show-toast', '⚠️ 目前選擇的模型不支援圖片上傳喔！');
    event.target.value = '';
    return;
  }

  const reader = new FileReader();
  
  reader.onload = (e) => {
    attachedFiles.value.push({
      name: file.name,
      type: file.type,
      data: e.target.result // 這是 Base64 字串
    });
  };
  reader.readAsDataURL(file);
  event.target.value = ''; // 清空 input 讓下次能選同一個檔案
};

// 移除預覽的檔案
const removeFile = (index) => {
  attachedFiles.value.splice(index, 1);
};

const handleSend = () => {
  // 防呆：如果輸入為空且沒有附件，或正在生成中，就不動作
  if ((!userInput.value.trim() && attachedFiles.value.length === 0) || props.isGenerating) return;
  
  // ⚠️ 往上傳遞的資料改成一個「物件」，包含文字與附件
  emit('send', { 
    text: userInput.value, 
    files: attachedFiles.value 
  });
  
  // 清空輸入框與附件
  userInput.value = '';
  attachedFiles.value = [];
};

// 處理選擇了提示詞的事件
const handleSelectPrompt = (promptText) => {
  // 1. 把提示詞附加到輸入框中 (如果有原本的字就換行)
  if (userInput.value.trim() !== '') {
    userInput.value += '\n\n';
  }
  userInput.value += promptText;
  
  // 2. 最保險的做法：直接在這裡把控制彈窗的變數設為 false！
  isPromptModalOpen.value = false;
};
</script>

<template>
  <div class="p-4 bg-white/80 backdrop-blur-md border-t border-gray-100">
    <div class="max-w-4xl mx-auto">
      
      <div v-if="attachedFiles.length > 0" class="flex gap-3 mb-3 overflow-x-auto pb-2">
        <div v-for="(file, index) in attachedFiles" :key="index" 
             class="relative group bg-gray-100 rounded-lg p-1 border border-gray-200 flex items-center justify-center w-16 h-16 shrink-0">
          <img v-if="file.type.startsWith('image/')" :src="file.data" class="w-full h-full object-cover rounded-md" />
          <div v-else class="text-xs text-gray-500 font-bold truncate max-w-full px-1">{{ file.name.split('.').pop().toUpperCase() }}</div>
          
          <button @click="removeFile(index)" 
                  class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity shadow-md">
            ✕
          </button>
        </div>
      </div>

      <div class="relative flex items-end shadow-sm rounded-xl border border-gray-300 bg-white overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500 transition-all">
        
        <input type="file" ref="fileInput" @change="handleFileChange" :accept="acceptedFileTypes" class="hidden" />
        <button @click="isPromptModalOpen = true"
                class="p-3 m-1 rounded-lg text-yellow-500 hover:bg-yellow-50 transition-colors flex shrink-0 self-end"
                title="提示詞模板庫">
          💡
        </button>
        <button @click="triggerFileSelect"
                :class="(props.supportsImage || props.supportsPdf) ? 'text-gray-400 hover:text-indigo-600 hover:bg-gray-50' : 'text-gray-300 cursor-not-allowed'"
                class="p-3 m-1 rounded-lg transition-colors flex shrink-0 self-end"
                title="上傳檔案">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
          </svg>
        </button>

        <textarea 
          v-model="userInput" 
          @keydown.enter.exact.prevent="handleSend"
          class="flex-1 px-2 pt-3 pb-4 leading-normal max-h-48 resize-none focus:outline-none bg-transparent"
          rows="1" 
          placeholder="輸入訊息...">
        </textarea>
        
        <div class="p-2 shrink-0 self-end">
          <button 
            @click="handleSend" 
            :disabled="isGenerating || (!userInput.trim() && attachedFiles.length === 0)"
            class="bg-indigo-600 text-white p-2.5 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 transition-colors flex items-center justify-center">
            <span class="font-medium px-2">發送</span>
          </button>
        </div>
      </div>
      
      <p class="text-center text-xs text-gray-400 mt-2">AI 生成內容可能不準確，請謹慎參考。請勿透露隱私訊息。</p>
    </div>
  </div>
  <PromptLibraryModal 
    :is-open="isPromptModalOpen" 
    @close="isPromptModalOpen = false"
    @select-prompt="handleSelectPrompt"
    @show-toast="(msg) => emit('show-toast', msg)"
  />
</template>