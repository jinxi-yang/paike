"""
AI智能体接口 - 预留接口供外部智能体对接
"""
from flask import Blueprint, jsonify, request
from config import Config
import requests
import re
import json

ai_bp = Blueprint('ai', __name__)


def call_ai_extract(prompt, context):
    """
    核心AI约束提取函数（可被其他模块导入调用）。
    
    Args:
        prompt: 用户输入的自然语言约束描述
        context: 排课上下文 dict，含 current_month, classes, teachers, homeroom_teachers
    
    Returns:
        (constraints_dict, error_string):
            成功时 constraints_dict 为解析后的约束字典，error_string 为 None
            失败时 constraints_dict 为 None，error_string 为错误信息
    """
    if not prompt or not prompt.strip():
        return {}, None

    # 构造组合Prompt
    full_query = f"""
    【用户指令】
    {prompt}

    【当前排课上下文】
    当前月份: {context.get('current_month', '2026-03')}
    活跃班级: {', '.join(context.get('classes', []))}
    讲师名单: {', '.join(context.get('teachers', []))}
    班主任名单: {', '.join(context.get('homeroom_teachers', []))}

    请根据上述信息提取排课约束，Strictly return VALID JSON ONLY.
    
    【实体识别规则】
    1. 当用户输入名字（如"王芳"）未明确指明身份时：
       - 优先在 [讲师名单] 和 [班主任名单] 中查找匹配项。
       - 如果只在 [讲师名单] 中，归为 `teacher_unavailable`。
       - 如果只在 [班主任名单] 中，归为 `homeroom_unavailable`。
    2. 如果名字同时出现在两个名单中：
       - 若用户指定了"班主任王芳"，则归为 `homeroom_unavailable`。
       - 若用户指定了"老师王芳"或未指定，优先视为讲师，归为 `teacher_unavailable`（除非上下文强烈暗示是班主任工作）。
    """

    ai_url = Config.AI_AGENT_URL
    api_key = getattr(Config, 'AI_AGENT_API_KEY', '')

    try:
        if not ai_url:
            raise ValueError("AI_AGENT_URL not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {
                "current_month": context.get('current_month', ''),
                "classes": json.dumps(context.get('classes', []), ensure_ascii=False),
                "teachers": json.dumps(context.get('teachers', []), ensure_ascii=False),
                "homeroom_teachers": json.dumps(context.get('homeroom_teachers', []), ensure_ascii=False),
                "raw_context": json.dumps(context, ensure_ascii=False)
            },
            "query": full_query,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "scheduler-system-user"
        }
        
        print("\n\n=== AI DEBUG: REQUEST ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        resp = requests.post(ai_url, json=payload, headers=headers, timeout=60)
        
        print("\n=== AI DEBUG: RESPONSE HEADERS ===")
        print(resp.headers)
        print("\n=== AI DEBUG: RESPONSE BODY ===")
        print(resp.text)
        print("=== END AI DEBUG ===\n")
        
        if resp.status_code != 200:
            return None, f'AI API Error: {resp.status_code} {resp.text}'
            
        resp_data = resp.json()
        ai_text = resp_data.get('answer', '')
        
        # 尝试从文本中提取JSON（增强：多种格式兼容）
        constraints = None
        
        # 模式1: ```json ... ```
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_text, re.DOTALL)
        # 模式2: ``` ... ```
        if not json_match:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', ai_text, re.DOTALL)
        # 模式3: 裸JSON对象
        if not json_match:
            json_match = re.search(r'(\{.*\})', ai_text, re.DOTALL)
            
        if json_match:
            json_str = json_match.group(1)
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            try:
                constraints = json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 模式4: 尝试直接解析全文
        if constraints is None:
            try:
                constraints = json.loads(ai_text)
            except (json.JSONDecodeError, ValueError):
                pass
        
        if constraints is not None:
            if 'constraints' in constraints:
                constraints = constraints['constraints']
            return constraints, None
        else:
            return None, f'无法解析AI返回的约束条件: {ai_text[:200]}'

    except Exception as e:
        print(f"AI Error: {e}")
        return None, str(e)


@ai_bp.route('/config', methods=['GET'])
def get_ai_config():
    """获取AI智能体配置状态"""
    return jsonify({
        'configured': bool(Config.AI_AGENT_URL),
        'url': Config.AI_AGENT_URL if Config.AI_AGENT_URL else None
    })


@ai_bp.route('/config', methods=['POST'])
def set_ai_config():
    """设置AI智能体URL（运行时修改，重启后失效）"""
    data = request.get_json()
    url = data.get('url', '')
    
    # 运行时修改配置
    Config.AI_AGENT_URL = url
    
    return jsonify({
        'success': True,
        'message': 'AI智能体URL已更新',
        'url': url
    })


@ai_bp.route('/schema', methods=['GET'])
def get_schema():
    """
    返回智能体需要提取的参数结构说明
    供开发智能体时参考
    """
    return jsonify({
        'description': '排课约束参数提取接口',
        'request_format': {
            'prompt': {
                'type': 'string',
                'description': '用户输入的自然语言提示词',
                'example': '3月25日北京有大型医疗峰会，医疗班那天不能上课。王芳老师3月21-22日请假了。'
            },
            'context': {
                'type': 'object',
                'description': '当前排课上下文信息',
                'fields': {
                    'current_month': '当前正在排课的月份，格式YYYY-MM',
                    'classes': '当前活跃的班级名称列表',
                    'teachers': '所有可用讲师名称列表'
                }
            }
        },
        'response_format': {
            'success': {
                'type': 'boolean',
                'description': '是否成功提取参数'
            },
            'constraints': {
                'type': 'object',
                'description': '提取出的排课约束',
                'fields': {
                    'blocked_dates': {
                        'type': 'array',
                        'description': '需要避开的日期列表',
                        'item_format': {
                            'date': '日期，格式YYYY-MM-DD（必填）',
                            'reason': '避开原因（必填）',
                            'affected_classes': '受影响的班级名称列表（可选，空表示所有班级）'
                        }
                    },
                    'teacher_unavailable': {
                        'type': 'array',
                        'description': '授课讲师请假/不可用 information',
                        'item_format': {
                            'teacher_name': '讲师姓名',
                            'dates': ['YYYY-MM-DD'],
                            'reason': '原因'
                        }
                    },
                    'homeroom_unavailable': {
                        'type': 'array',
                        'description': '班主任请假/不可用 information',
                        'item_format': {
                            'homeroom_name': '班主任姓名',
                            'dates': ['YYYY-MM-DD'],
                            'reason': '原因'
                        }
                    },
                    'preferred_dates': {
                        'type': 'array',
                        'description': '优先排课日期建议',
                        'item_format': {
                            'class_name': '班级名称',
                            'preferred_date': '建议日期，格式YYYY-MM-DD',
                            'reason': '建议原因'
                        }
                    },
                    'merge_suggestions': {
                        'type': 'array',
                        'description': '合班建议',
                        'item_format': {
                            'classes': '建议合班的班级名称列表',
                            'topic': '合班的课题名称',
                            'suggested_date': '建议合班日期'
                        }
                    },
                    'special_notes': {
                        'type': 'string',
                        'description': '其他备注信息'
                    }
                }
            }
        },
        'example_extraction': {
            'input_prompt': '3月25日北京有大型医疗峰会，医疗班那天不能上课。讲师王芳3月21-22日请假了。班主任李婷婷4月12日请假。',
            'expected_output': {
                'success': True,
                'constraints': {
                    'blocked_dates': [
                        {
                            'date': '2026-03-25',
                            'reason': '北京大型医疗峰会',
                            'affected_classes': ['医疗产业实战班']
                        }
                    ],
                    'teacher_unavailable': [
                        {
                            'teacher_name': '王芳',
                            'dates': ['2026-03-21', '2026-03-22'],
                            'reason': '请假'
                        }
                    ],
                    'homeroom_unavailable': [
                        {
                            'homeroom_name': '李婷婷',
                            'dates': ['2026-04-12'],
                            'reason': '请假'
                        }
                    ],
                    'preferred_dates': [],
                    'merge_suggestions': [],
                    'special_notes': ''
                }
            }
        }
    })
