#!/usr/bin/env python3
"""Fix line 2157 in index.html."""

filepath = r'd:\学习\outputmsg\排课\paike\frontend\index.html'

with open(filepath, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# The correct line should be a JS template literal with backticks:
# msg += `\n\n注意：有 ${genResult.skipped.length} 个班级未能安排档期，详情请见左侧提示面板。`;
correct_line = '                    msg += `\\n\\n\u6ce8\u610f\uff1a\u6709 ${genResult.skipped.length} \u4e2a\u73ed\u7ea7\u672a\u80fd\u5b89\u6392\u6863\u671f\uff0c\u8be6\u60c5\u8bf7\u89c1\u5de6\u4fa7\u63d0\u793a\u9762\u677f\u3002`;\r\n'

print("Before:", repr(lines[2156]))
lines[2156] = correct_line
print("After:", repr(lines[2156]))

with open(filepath, 'w', encoding='utf-8-sig') as f:
    f.writelines(lines)

print("Done!")
