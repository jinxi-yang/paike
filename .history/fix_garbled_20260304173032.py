#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix garbled Chinese text in index.html."""

filepath = r'd:\学习\outputmsg\排课\paike\frontend\index.html'

with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Define all replacements: (garbled, correct)
replacements = []

# Check what's on each line to find the exact garbled strings
lines = content.split('\n')
for i, line in enumerate(lines):
    # Print lines with unusual chars for debugging
    for ch in line:
        if ord(ch) > 0x9000 and ch not in '需要的正常字':
            pass

# Direct string replacements
# Line 474: combo modal comment  
# Find the exact garbled text by searching for surrounding context
for i, line in enumerate(lines):
    if 'add-combo-modal' in line and i > 0:
        prev = lines[i-1]
        if '<!--' in prev and '-->' in prev and '课组合' not in prev.replace('课组合弹窗', ''):
            lines[i-1] = '    <!-- 新增教课组合弹窗 -->\r'
            print(f"Fixed line {i}: combo modal comment")
            break

# Line ~936: 或未分类的课?
for i, line in enumerate(lines):
    if '或未分类的课?' in line:
        lines[i] = line.replace('或未分类的课?', '或未分类的课程')
        print(f"Fixed line {i+1}: 或未分类的课程")
    if '目标周的周?' in line:
        lines[i] = lines[i].replace('目标周的周?', '目标周的周六')
        print(f"Fixed line {i+1}: 目标周的周六")

# Line ~1182: 瑙嗗浘鐘舵€佺鐞? -> 视图状态管理
for i, line in enumerate(lines):
    if '瑙嗗浘鐘舵' in line:
        lines[i] = line.replace('瑙嗗浘鐘舵€佺鐞?', '视图状态管理')
        # Also try without the trailing ?
        if '瑙嗗浘鐘舵' in lines[i]:
            # Replace whatever variant
            import re
            lines[i] = re.sub(r'瑙嗗浘鐘舵[^\s=]*', '视图状态管理', lines[i])
        print(f"Fixed line {i+1}: 视图状态管理")

# Line ~1193: 如果还在范围内?
for i, line in enumerate(lines):
    if '如果还在范围内?' in line:
        lines[i] = line.replace('如果还在范围内?', '如果还在范围内）')
        print(f"Fixed line {i+1}: 如果还在范围内）")

# Line ~1201: 请棢查后端服
for i, line in enumerate(lines):
    if '请棢查后端服' in line:
        lines[i] = line.replace('请棢查后端服', '请检查后端服务')
        print(f"Fixed line {i+1}: 请检查后端服务")

# Lines ~1506, 1640: 按月规划全学期排课进
for i, line in enumerate(lines):
    if '按月规划全学期排课进<' in line or line.strip().endswith('按月规划全学期排课进'):
        lines[i] = line.replace('按月规划全学期排课进', '按月规划全学期排课进度')
        print(f"Fixed line {i+1}: 按月规划全学期排课进度")

# Line ~1642: 淇濆瓨鑽夌 -> 保存草稿
for i, line in enumerate(lines):
    if '淇濆瓨鑽' in line:
        import re
        lines[i] = re.sub(r'淇濆瓨鑽夌\S*', '保存草稿', lines[i])
        if '淇濆瓨鑽' in lines[i]:
            lines[i] = re.sub(r'淇濆瓨鑽[^\s<]*', '保存草稿', lines[i])
        print(f"Fixed line {i+1}: 保存草稿")

# Line ~1666: 鏃ユ湡 -> 日期, 褰卞搷鑼冨洿 -> 影响范围
for i, line in enumerate(lines):
    if '鏃ユ湡' in line and '褰卞搷' in line:
        lines[i] = line.replace('鏃ユ湡', '日期').replace('褰卞搷鑼冨洿', '影响范围')
        print(f"Fixed line {i+1}: 日期/影响范围")
    elif '鏃ユ湡' in line and '鏌ョ' not in line:
        # Other uses of 鏃ユ湡
        pass

# Line ~1668: 鏌ョ湅鍘熷洜 -> 查看原因
for i, line in enumerate(lines):
    if '鏌ョ湅鍘熷洜' in line:
        lines[i] = line.replace('鏌ョ湅鍘熷洜', '查看原因')
        print(f"Fixed line {i+1}: 查看原因")

# Line ~1671: 鍘熷洜 -> 原因
for i, line in enumerate(lines):
    if '鍘熷洜' in line:
        lines[i] = line.replace('鍘熷洜:', '原因:').replace('鍘熷洜', '原因')
        print(f"Fixed line {i+1}: 原因")

# Line ~1675: 无无法解决冲 -> 无无法解决冲突
for i, line in enumerate(lines):
    if '无无法解决冲<' in line or '无无法解决冲突' not in line and '无无法解决冲' in line:
        lines[i] = line.replace('无无法解决冲', '无无法解决冲突')
        print(f"Fixed line {i+1}: 无无法解决冲突")

# Line ~1679: 鏃犲緟纭椤 -> 无待确认项
for i, line in enumerate(lines):
    if '鏃犲緟' in line:
        import re
        lines[i] = re.sub(r'鏃犲緟纭椤\S*', '无待确认项', lines[i])
        if '鏃犲緟' in lines[i]:
            lines[i] = re.sub(r'鏃犲緟[^\s<"\']*', '无待确认项', lines[i])
        print(f"Fixed line {i+1}: 无待确认项")

# Line ~1681: 已解?...椤 -> 已解决 N 项, 鏃犲凡瑙ｅ喅椤 -> 无已解决项
for i, line in enumerate(lines):
    if '鏃犲凡瑙' in line:
        import re
        lines[i] = re.sub(r'鏃犲凡瑙[^\s<"\']*', '无已解决项', lines[i])
        print(f"Fixed line {i+1}: 无已解决项")
    # 已解? X 椤
    if '椤' in line and '已解' in line and '已解决' not in line:
        lines[i] = lines[i].replace('已解?', '已解决 ').replace('椤', '项')
        print(f"Fixed line {i+1}: 已解决 N 项")

# Line ~1690: 待确 -> 待确认
for i, line in enumerate(lines):
    if '>待确<' in line:
        lines[i] = line.replace('>待确<', '>待确认<')
        print(f"Fixed line {i+1}: 待确认")

# Line ~1694: 已解 -> 已解决 (in section header)
for i, line in enumerate(lines):
    if '>已解<' in line:
        lines[i] = line.replace('>已解<', '>已解决<')
        print(f"Fixed line {i+1}: 已解决")

# Line ~1757: 骞? -> 年
for i, line in enumerate(lines):
    if '骞?' in line:
        lines[i] = line.replace('骞?', '年')
        print(f"Fixed line {i+1}: 年")

# Lines ~1772, 1778: 鏃 -> 无
for i, line in enumerate(lines):
    if '>鏃<' in line:
        lines[i] = line.replace('>鏃<', '>无<')
        print(f"Fixed line {i+1}: 无")

# Line ~1885: 鏇存柊纭鎸夐挳鐘舵€? -> 更新确认按钮状态
for i, line in enumerate(lines):
    if '鏇存柊纭' in line:
        import re
        lines[i] = re.sub(r'鏇存柊纭鎸夐挳鐘舵[^\n\r]*', '更新确认按钮状态', lines[i])
        if '鏇存柊纭' in lines[i]:
            lines[i] = re.sub(r'鏇存柊纭[^\n\r]*', '更新确认按钮状态', lines[i])
        print(f"Fixed line {i+1}: 更新确认按钮状态")

# Line ~1896: 屢部重新渲染过于复杂 -> 重新渲染过于复杂
for i, line in enumerate(lines):
    if '屢部重新渲染' in line:
        lines[i] = line.replace('屢部重新渲染', '重新渲染')
        print(f"Fixed line {i+1}: 重新渲染过于复杂")

# Line ~1915: 逢出合并模? -> 退出合并模式
for i, line in enumerate(lines):
    if '逢出合并模?' in line or '逢出合并模' in line:
        lines[i] = line.replace('逢出合并模?', '退出合并模式').replace('逢出合并模', '退出合并模式')
        print(f"Fixed line {i+1}: 退出合并模式")

# Line ~1959: 可选教-课组? -> 可选教-课组合
for i, line in enumerate(lines):
    if '可选教-课组?' in line:
        lines[i] = line.replace('可选教-课组?', '可选教-课组合')
        print(f"Fixed line {i+1}: 可选教-课组合")

# Line ~1963: 填充下拉? -> 填充下拉框
for i, line in enumerate(lines):
    if '填充下拉?' in line:
        lines[i] = line.replace('填充下拉?', '填充下拉框')
        print(f"Fixed line {i+1}: 填充下拉框")

# Line ~2057: 无特殊要求"处? -> 无特殊要求"处理
for i, line in enumerate(lines):
    if '无特殊要求"处?' in line or "无特殊要求" in line and "处?" in line:
        lines[i] = line.replace('处?', '处理')
        print(f"Fixed line {i+1}: 处理")

# Line ~2059: 描?无特殊要? -> 描述"无特殊要求"
for i, line in enumerate(lines):
    if '描?' in line and '无特殊要?' in line:
        lines[i] = line.replace('描?', '描述"').replace('无特殊要?', '无特殊要求"')
        print(f"Fixed line {i+1}: 描述无特殊要求")

# Line ~2070: 准备上下文数? -> 准备上下文数据
for i, line in enumerate(lines):
    if '准备上下文数?' in line:
        lines[i] = line.replace('准备上下文数?', '准备上下文数据')
        print(f"Fixed line {i+1}: 准备上下文数据")

# Line ~2088: 鎻愬彇绾︽潫 -> 提取约束
for i, line in enumerate(lines):
    if '鎻愬彇绾' in line:
        import re
        lines[i] = re.sub(r'鎻愬彇绾︽潫', '提取约束', lines[i])
        if '鎻愬彇绾' in lines[i]:
            lines[i] = re.sub(r'鎻愬彇绾[^\n\r]*', '提取约束', lines[i])
        print(f"Fixed line {i+1}: 提取约束")

# Line ~2102: 鏄剧ず鎻愬彇缁撴灉 -> 显示提取结果
for i, line in enumerate(lines):
    if '鏄剧ず鎻' in line:
        import re
        lines[i] = re.sub(r'鏄剧ず鎻愬彇缁撴灉', '显示提取结果', lines[i])
        if '鏄剧ず鎻' in lines[i]:
            lines[i] = re.sub(r'鏄剧ず鎻[^\n\r]*', '显示提取结果', lines[i])
        print(f"Fixed line {i+1}: 显示提取结果")

# Line ~2106: 閬垮紑鏃ユ湡锛? -> 避开日期：
for i, line in enumerate(lines):
    if '閬垮紑鏃ユ湡' in line:
        import re
        lines[i] = re.sub(r'閬垮紑鏃ユ湡锛[^<]*', '避开日期：', lines[i])
        if '閬垮紑' in lines[i]:
            lines[i] = re.sub(r'閬垮紑[^<]*', '避开日期：', lines[i])  
        print(f"Fixed line {i+1}: 避开日期")

# Line ~2109: 讲师请假? -> 讲师请假：
for i, line in enumerate(lines):
    if '讲师请假?' in line:
        lines[i] = line.replace('讲师请假?', '讲师请假：')
        print(f"Fixed line {i+1}: 讲师请假：")

# Line ~2120: 应用约? -> 应用约束
for i, line in enumerate(lines):
    if '应用约?' in line:
        lines[i] = line.replace('应用约?', '应用约束')
        print(f"Fixed line {i+1}: 应用约束")

# Line ~2138: 未排课的班? -> 未排课的班级
for i, line in enumerate(lines):
    if '未排课的班?' in line:
        lines[i] = line.replace('未排课的班?', '未排课的班级')
        print(f"Fixed line {i+1}: 未排课的班级")

# Line ~2156: 纭繚鏄剧ず -> 确保显示
for i, line in enumerate(lines):
    if '纭繚鏄剧ず' in line:
        lines[i] = line.replace('纭繚鏄剧ず', '确保显示')
        print(f"Fixed line {i+1}: 确保显示")

# Line ~2235: 含课? -> 含课题
for i, line in enumerate(lines):
    if '含课?' in line:
        lines[i] = line.replace('含课?', '含课题')
        print(f"Fixed line {i+1}: 含课题")

# Line ~2244: 课题下拉? -> 课题下拉框
for i, line in enumerate(lines):
    if '课题下拉?' in line:
        lines[i] = line.replace('课题下拉?', '课题下拉框')
        print(f"Fixed line {i+1}: 课题下拉框")

# Lines ~2248, 2268: 筛选? -> 筛选值
for i, line in enumerate(lines):
    if '筛选?' in line:
        lines[i] = line.replace('筛选?', '筛选值')
        print(f"Fixed line {i+1}: 筛选值")

# Line ~2276: 展示课? -> 展示课程
for i, line in enumerate(lines):
    if '展示课?' in line:
        lines[i] = line.replace('展示课?', '展示课程')
        print(f"Fixed line {i+1}: 展示课程")

# Line ~2284: 再分? -> 再分组
for i, line in enumerate(lines):
    if '再分?' in line:
        lines[i] = line.replace('再分?', '再分组')
        print(f"Fixed line {i+1}: 再分组")

# Line ~2315: 类型标? -> 类型标题
for i, line in enumerate(lines):
    if '类型标?' in line:
        lines[i] = line.replace('类型标?', '类型标题')
        print(f"Fixed line {i+1}: 类型标题")

# Line ~2366: 未分类课< -> 未分类课程
for i, line in enumerate(lines):
    if '未分类课<' in line:
        lines[i] = line.replace('未分类课<', '未分类课程<')
        print(f"Fixed line {i+1}: 未分类课程")

# Line ~2417: 娣诲姞澶辫触 -> 添加失败
for i, line in enumerate(lines):
    if '娣诲姞澶辫触' in line:
        lines[i] = line.replace('娣诲姞澶辫触', '添加失败')
        print(f"Fixed line {i+1}: 添加失败")

# Line ~2420: 娣诲姞閿欒 -> 添加错误
for i, line in enumerate(lines):
    if '娣诲姞閿欒' in line:
        lines[i] = line.replace('娣诲姞閿欒', '添加错误')
        print(f"Fixed line {i+1}: 添加错误")

# Write back
new_content = '\n'.join(lines)
# Preserve BOM if it was there
with open(filepath, 'w', encoding='utf-8-sig') as f:
    f.write(new_content)

print("\nAll fixes applied!")
