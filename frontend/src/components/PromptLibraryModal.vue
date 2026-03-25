<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  isOpen: Boolean
});

const emit = defineEmits(['close', 'select-prompt', 'show-toast']);

const prompts = ref([]);
const isAdding = ref(false);
const newTitle = ref('');
const newContent = ref('');

// 取得後端 API 網址 (請確認你的 port 是 8000)
const API_BASE_URL = 'http://localhost:8000/api';

// 1. 取得所有提示詞
const fetchPrompts = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/prompts`);
    if (res.ok) {
      prompts.value = await res.json();
    }
  } catch (error) {
    console.error("無法取得提示詞:", error);
    emit('show-toast', '❌ 無法載入提示詞庫');
  }
};

// 2. 新增提示詞
const savePrompt = async () => {
  if (!newTitle.value.trim() || !newContent.value.trim()) {
    emit('show-toast', '⚠️ 標題與內容不能為空！');
    return;
  }
  try {
    const res = await fetch(`${API_BASE_URL}/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle.value, content: newContent.value })
    });
    if (res.ok) {
      const savedPrompt = await res.json();
      prompts.value.push(savedPrompt); // 更新畫面
      newTitle.value = '';
      newContent.value = '';
      isAdding.value = false;
      emit('show-toast', '✅ 成功新增提示詞！');
    }
  } catch (error) {
    console.error("新增失敗:", error);
    emit('show-toast', '❌ 新增失敗');
  }
};

// 3. 刪除提示詞
const deletePrompt = async (id) => {
  if (!confirm('確定要刪除這個模板嗎？')) return;
  try {
    const res = await fetch(`${API_BASE_URL}/prompts/${id}`, { method: 'DELETE' });
    if (res.ok) {
      prompts.value = prompts.value.filter(p => p.id !== id);
      emit('show-toast', '🗑️ 模板已刪除');
    }
  } catch (error) {
    console.error("刪除失敗:", error);
    emit('show-toast', '❌ 刪除失敗');
  }
};

// 4. 點擊套用提示詞
const selectPrompt = (content) => {
  emit('select-prompt', content);
  emit('close'); // 套用後自動關閉視窗
};

// 元件載入時抓取資料
onMounted(() => {
  fetchPrompts();
});
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 z-50 flex justify-center items-center backdrop-blur-sm p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
      
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 class="text-lg font-bold text-gray-800 flex items-center gap-2">
          💡 提示詞模板庫
        </h3>
        <button @click="emit('close')" class="text-gray-400 hover:text-red-500 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 overflow-y-auto flex-1 bg-gray-50">
        
        <div class="mb-6">
          <button v-if="!isAdding" @click="isAdding = true" class="w-full py-3 border-2 border-dashed border-indigo-200 text-indigo-600 rounded-xl hover:bg-indigo-50 transition-colors font-medium flex justify-center items-center gap-2">
            <span>➕ 新增自訂模板</span>
          </button>
          
          <div v-else class="bg-white p-4 rounded-xl shadow-sm border border-indigo-100">
            <input v-model="newTitle" type="text" placeholder="模板標題 (例：專業翻譯)" class="w-full mb-3 p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
            <textarea v-model="newContent" placeholder="請輸入完整的 Prompt 內容..." rows="3" class="w-full mb-3 p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none"></textarea>
            <div class="flex justify-end gap-2">
              <button @click="isAdding = false" class="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
              <button @click="savePrompt" class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium">儲存模板</button>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div v-if="prompts.length === 0" class="text-center py-8 text-gray-400">
            目前還沒有模板，趕快新增一個吧！
          </div>
          
          <div v-for="prompt in prompts" :key="prompt.id" class="group bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:border-indigo-300 transition-all flex flex-col gap-2 relative">
            <div class="flex justify-between items-start">
              <h4 class="font-bold text-gray-800">{{ prompt.title }}</h4>
              <button @click="deletePrompt(prompt.id)" class="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity" title="刪除">🗑️</button>
            </div>
            <p class="text-sm text-gray-500 line-clamp-2">{{ prompt.content }}</p>
            <button @click="selectPrompt(prompt.content)" class="mt-2 w-full py-2 bg-gray-50 text-indigo-600 text-sm rounded-lg hover:bg-indigo-600 hover:text-white transition-colors font-medium">
              套用此模板
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>