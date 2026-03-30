import re

with open('d:\\学习\\outputmsg\\排课\\paike\\frontend\\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "// 标2：显示讲师搜索下拉"
end_marker = "cc.innerHTML = '<span class=\"text-[10px] text-slate-400 italic mt-0.5\">加载课程中...</span>';"

new_code = """
        // 标2：显示讲师搜索下拉
        let cachedAllTeachers = [];
        async function showTeacherSearchDropdown(e, topicId) {
            e.stopPropagation();
            const dp = document.getElementById(`quick-add-teacher-dropdown-${topicId}`);
            
            // 关闭其他所有下拉
            document.querySelectorAll('[id^=quick-add-teacher-dropdown-]').forEach(el => { if(el !== dp) el.classList.add('hidden'); });
            
            if (!dp.classList.contains('hidden')) {
                dp.classList.add('hidden');
                return;
            }
            dp.classList.remove('hidden');
            
            const input = document.getElementById(`quick-add-teacher-input-${topicId}`);
            input.value = ''; // 展开时清空搜索
            setTimeout(() => input.focus(), 50); // 聚集焦点
            
            const listEl = document.getElementById(`quick-add-teacher-list-${topicId}`);
            
            if (cachedAllTeachers.length === 0) {
                listEl.innerHTML = '<div class="p-2 text-xs text-slate-400">加载中...</div>';
                try {
                    const r = await fetch(`${API_BASE}/teachers`);
                    cachedAllTeachers = await r.json();
                } catch(e) {}
            }
            renderTeacherSearchDropdown(topicId, '');
        }

        function filterTeacherSearchDropdown(topicId) {
            const val = document.getElementById(`quick-add-teacher-input-${topicId}`);
            renderTeacherSearchDropdown(topicId, val);
        }

        function renderTeacherSearchDropdown(topicId, keyword) {
            const listEl = document.getElementById(`quick-add-teacher-list-${topicId}`);
            keyword = (keyword || '').toLowerCase().trim();
            const list = cachedAllTeachers.filter(t => t.name.toLowerCase().includes(keyword));
            
            if (list.length === 0) {
                listEl.innerHTML = '<div class="p-2 text-xs text-slate-400">无匹配讲师</div>';
                return;
            }
            listEl.innerHTML = list.map(t => `
                <div class="px-2 py-1.5 text-xs text-slate-700 hover:bg-blue-50 cursor-pointer border-b border-slate-50 last:border-0" onclick="selectTeacherSearch(event, ${topicId}, ${t.id}, '${t.name}')">
                    ${t.name}
                </div>
            `).join('');
        }

        // 标2：选中讲师
        async function selectTeacherSearch(e, topicId, teacherId, teacherName) {
            e.stopPropagation();
            
            // 更新显示和隐藏值
            const btnDisp = document.getElementById(`quick-add-teacher-display-${topicId}`);
            if (btnDisp) {
                btnDisp.textContent = teacherName;
                btnDisp.classList.replace('text-slate-400', 'text-slate-700'); // 改变颜色表示已选定
            }
            
            document.getElementById(`quick-add-teacher-val-${topicId}`).value = teacherId;
            document.getElementById(`quick-add-teacher-dropdown-${topicId}`).classList.add('hidden');
            
            const cc = document.getElementById(`quick-add-courses-container-${topicId}`);
            cc.innerHTML = '<span class="text-[10px] text-slate-400 italic mt-0.5">加载课程中...</span>';
"""

pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
text = pattern.sub(new_code.strip(), text)

with open('d:\\学习\\outputmsg\\排课\\paike\\frontend\\index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("successfully patched JS")
