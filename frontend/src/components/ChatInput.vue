<script setup>
import { ref } from 'vue';

// 接收 App.vue 傳來的狀態 (例如：AI 是否正在生成中，若是，則禁用按鈕)
const props = defineProps({
  isGenerating: {
    type: Boolean,
    default: false
  }
});

// 定義要往上傳遞的事件 (發送訊息)
const emit = defineEmits(['send']);

// 輸入框的狀態現在由這個小組件自己管理就好了！
const userInput = ref('');

const handleSend = () => {
  // 防呆：如果輸入為空，或正在生成中，就不動作
  if (!userInput.value.trim() || props.isGenerating) return;
  
  // 把使用者輸入的文字「往上廣播」給 App.vue
  emit('send', userInput.value);
  
  // 清空輸入框
  userInput.value = '';
};
</script>

<template>
  <div class="p-4 bg-white/80 backdrop-blur-md border-t border-gray-100">
    <div class="max-w-4xl mx-auto relative flex items-end shadow-sm rounded-xl border border-gray-300 bg-white overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500 transition-all">
      <textarea 
        v-model="userInput" 
        @keydown.enter.exact.prevent="handleSend"
        class="flex-1 px-4 pt-3 pb-4 leading-normal max-h-48 resize-none focus:outline-none bg-transparent"
        rows="1" 
        placeholder="輸入訊息...">
      </textarea>
      <div class="p-2">
        <button 
          @click="handleSend" 
          :disabled="isGenerating || !userInput.trim()"
          class="bg-indigo-600 text-white p-2.5 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 transition-colors flex items-center justify-center">
          <span class="font-medium px-2">發送</span>
        </button>
      </div>
    </div>
    <p class="text-center text-xs text-gray-400 mt-2">AI 生成內容可能不準確，請謹慎參考。請勿透露隱私訊息。</p>
  </div>
</template>