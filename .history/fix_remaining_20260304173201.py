#!/usr/bin/env python3
"""Fix remaining garbled lines by line index."""

filepath = r'd:\学习\outputmsg\排课\paike\frontend\index.html'

with open(filepath, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Fix line 474 (index 473) - combo modal comment
lines[473] = '    <!-- 新增教课组合弹窗 -->\n'
print("Fixed line 474: 新增教课组合弹窗")

# Fix line 2106 (index 2105) - blocked dates display
lines[2105] = "                        html += '<div class=\"mb-1\">📅 <strong>避开日期：</strong>' + data.constraints.blocked_dates.map(d => `${d.date}(${d.reason})`).join(', ') + '</div>';\n"
print("Fixed line 2106: 避开日期")

# Fix line 2109 (index 2108) - teacher unavailable display
lines[2108] = "                        html += '<div class=\"mb-1\">🚫 <strong>讲师请假：</strong>' + data.constraints.teacher_unavailable.map(t => `${t.teacher_name}: ${t.dates.join(',')}`).join('; ') + '</div>';\n"
print("Fixed line 2109: 讲师请假")

# Also check for line 2156 (纭繚鏄剧ず -> 确保显示) - verify it's already fixed
if '纭繚鏄剧ず' in lines[2155]:
    lines[2155] = lines[2155].replace('纭繚鏄剧ず', '确保显示')
    print("Fixed line 2156: 确保显示")

with open(filepath, 'w', encoding='utf-8-sig') as f:
    f.writelines(lines)

print("\nDone! Remaining fixes applied.")
