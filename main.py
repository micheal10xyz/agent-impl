import re
import json

def extract_action(text):
    pattern = r"Action:\s*(\{.*\})"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        print("没有匹配到 Action")
        return None
    action_json_str = match.group(1)
    print(action_json_str)
    try:
        action_data = json.loads(action_json_str)
        return action_data
    except json.JSONDecodeError:
        print("JSON 解析失败")
        return None

input_string = """Thought: 我需要先计算 1+2。  
Action: {
    "tool_name": "add_tool",
    "arguments": {"a": 1, "b": 2}
}
"""

result = extract_action(input_string)
print("提取结果:", result)
