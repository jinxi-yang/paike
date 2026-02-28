
import os

file_path = r'D:\项目\AI\北清商学院\paike\frontend\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_index = -1
end_index = -1

# Find start
for i, line in enumerate(lines):
    if 'function renderMonthSchedule(data) {' in line:
        start_index = i
        break

# Find end (search for the next function or section header after start)
# The next section is "// ==================== 合班逻辑 ===================="
if start_index != -1:
    for i in range(start_index, len(lines)):
        if '// ==================== 合班逻辑 ====================' in line: # This loop variable 'line' is stale
            pass 
        if '// ==================== 合班逻辑 ====================' in lines[i]:
            end_index = i - 1 # The line before the header is usually empty, the one before is '}'
            break

# Refine end_index to point to the closing brace of the function
# We look backwards from the section header
if end_index != -1:
    while end_index > start_index:
        if lines[end_index].strip() == '}':
            break
        end_index -= 1

if start_index != -1 and end_index != -1:
    print(f"Replacing lines {start_index+1} to {end_index+1}")
    
    new_content = """        function renderMonthSchedule(data) {
            const container = document.getElementById('schedule-container');
            const weeks = data.weeks || [];
            
            if (weeks.length === 0) {
                 container.innerHTML = '<div class="text-center text-slate-400 p-8">本月暂无排课</div>';
                 return;
            }
            container.innerHTML = weeks.map((w, idx) => {
                const weekStart = new Date(w.week_start);
                const weekEnd = new Date(w.week_end);
                const dateRangeStr = `${weekStart.getMonth()+1}/${weekStart.getDate()} - ${weekEnd.getMonth()+1}/${weekEnd.getDate()}`;

                let contentHtml = '';
                if (w.schedules.length === 0) {
                    contentHtml = `<div class="text-center p-4 border-2 border-dashed border-slate-200 rounded-lg text-slate-400 text-sm select-none h-[80px] flex items-center justify-center">本周无排课 (可拖入课程)</div>`;
                } else {
                    contentHtml = w.schedules.map(s => {
                         // Calculate 2-day range for display
                        const d1 = new Date(s.scheduled_date);
                        const d2 = new Date(d1); 
                        d2.setDate(d1.getDate() + 1);
                        const dateDisplay = `${d1.getMonth()+1}/${d1.getDate()} - ${d2.getDate()}`;
                        
                        // Merge styling
                        const isSelected = selectedMergeIds.has(s.id);
                        const selectStyle = isSelected ? 'ring-2 ring-purple-500 bg-purple-50' : '';
                        const cursorStyle = isMergeMode ? 'cursor-pointer hover:bg-slate-50' : '';


                        return `
                        <div class="draggable p-3 bg-white border ${s.merged_with ? 'border-t-4 border-t-purple-500' : (s.status === 'completed' ? 'border-green-200' : 'border-blue-200')} rounded-lg hover:shadow-md transition-all cursor-move mb-2 ${selectStyle} ${cursorStyle}"
                             draggable="true" data-schedule-id="${s.id}" data-week="${w.week_start}"
                             onclick="${isMergeMode ? `toggleMergeSelect(${s.id})` : ''}">
                            <div class="flex items-start justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 rounded-full ${s.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'} flex items-center justify-center font-bold text-sm text-center">${s.topic_sequence || s.week_number}</div>
                                    <div>
                                        <div class="font-medium text-sm">${s.topic_name}</div>
                                        <div class="text-[10px] text-slate-500 font-bold mt-0.5" title="周六至周日">${dateDisplay} (2天)</div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    ${s.combo ? `<div class="text-xs text-blue-600 font-semibold">${s.combo.teacher_name}</div><div class="text-[10px] text-slate-500">${s.combo.course_name}</div>` : '<div class="text-[10px] text-orange-500">待分配</div>'}
                                </div>
                            </div>
                            ${s.merged_with ? '<div class="text-[9px] bg-purple-100 text-purple-600 px-2 py-0.5 rounded inline-block mt-1">合班</div>' : ''}
                            ${isSelected ? '<div class="absolute top-2 right-2 text-purple-600"><i data-lucide="check-circle" class="w-5 h-5"></i></div>' : ''}

                            <div class="mt-2 flex gap-2 pt-2 border-t border-slate-100 justify-end">
                                <button onclick="openAdjustModal(${s.id}); event.stopPropagation();" class="text-[10px] px-2 py-0.5 bg-indigo-100 text-indigo-600 rounded hover:bg-indigo-200">调整</button>
                                ${s.merged_with ? `<button onclick="unmergeSchedule(${s.id}); event.stopPropagation();" class="text-[10px] px-2 py-0.5 bg-purple-100 text-purple-600 rounded hover:bg-purple-200">拆分</button>` : ''}
                                <button onclick="deleteScheduleItem(${s.id}); event.stopPropagation();" class="text-[10px] px-2 py-0.5 bg-red-100 text-red-600 rounded hover:bg-red-200">删除</button>
                            </div>
                        </div>
                    `}).join('');
                }

                return `
                    <div class="bg-slate-50 border rounded-xl p-4 mb-4">
                        <h4 class="font-bold text-sm text-slate-700 mb-3 flex justify-between">
                            <span>第 ${idx + 1} 周 · ${dateRangeStr}</span>
                            <span class="text-xs font-normal text-slate-400 bg-white px-2 py-0.5 rounded border">可拖拽排课</span>
                        </h4>
                        <div class="drop-zone min-h-[50px]" data-week="${w.week_start}">
                            ${contentHtml}
                        </div>
                    </div>
                `;
            }).join('');

            // 初始化拖拽事件
            initDragAndDrop();

            // 如果处于合并模式，显示选择按钮
            if (isMergeMode) {
                document.querySelectorAll('.merge-select-btn').forEach(btn => btn.classList.remove('hidden'));
            }
        }
"""
    # Insert new lines
    # We replace from start_index to end_index (inclusive)
    
    # Split new_content into lines and add newline
    new_lines = [l + '\\n' for l in new_content.split('\\n')]
    
    # We slice: lines[:start_index] + new_lines + lines[end_index+1:]
    # Check if end_index is the closing brace '}'
    # If lines[end_index] is '        }', we replace it.
    
    final_lines = lines[:start_index] + new_lines + lines[end_index+1:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    print("Success")
else:
    print("Start or End not found")
