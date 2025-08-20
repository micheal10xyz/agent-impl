# calculator_agent.py
import openai
import asyncio
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp import Client
import json
import logging
import gradio as gr
import re


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

system_prompt = """
你是一个遵循 ReAct 框架的智能Agent。  
你的任务是通过 **思考（Thought）- 行动（Action）- 观察（Observation）- 思考** 的循环，逐步完成用户的指令。  

### 你的推理流程
1. **Thought（思考）**  
   - 分析当前情况，决定下一步要做什么。  
   - 思考内容应简洁，直观，解释你为什么要调用某个工具或直接得出答案。  

2. **Action（行动）**  
   - 如果需要调用工具，你必须输出一个 JSON 对象，格式如下：  
     ```
     Action: {
         "tool_name": "<工具名称>",
         "arguments": {<参数字典>}
     }
     ```
   - 工具名称和参数必须完全正确，确保 JSON 可以被外部程序解析。  

3. **Observation（观察）**  
   - Action 执行后，外部环境会将结果作为 Observation 返回给你。  
   - 你 **绝对不能自己生成 Observation**，只能等待外部提供。  

4. **循环继续**  
   - 收到 Observation 后，你需要重新输出 Thought，分析结果，并决定下一步 Action，直到完成任务。  

5. **Final Answer（最终答案）**  
   - 当你已经得到完整答案时，必须停止推理，输出：  
     ```
     Final Answer: <最终答案>
     ```

### 输出规则
- 每一步推理只能包含 **一个 Thought** 和 **一个 Action**，禁止合并多个。  
- 如果不需要再调用工具，可以直接输出 **Final Answer**。  
- 你不能输出与 Thought/Action/Final Answer 以外的内容。  
- 严禁自行编造 Observation。  

### 示例
用户问题：计算 (2+3) * 4  

你的输出过程应为：  

Thought: 我需要先计算 2+3。  
Action: {
    "tool_name": "add_tool",
    "arguments": {"a": 2, "b": 3}
}

Observation: 5 （外部工具执行结果， 不是你返回的）

Thought: 我得到 2+3=5，现在需要计算 5*4。  
Action: {
    "tool_name": "mul_tool",
    "arguments": {"a": 5, "b": 4}
}

Observation: 20 （外部工具执行结果， 不是你返回的）

Thought: 我已经得到最终结果。  
Final Answer: 20


### 工具列表
{{tools}}

"""

model_client = openai.AsyncOpenAI(api_key='sk-e259258120804170b6809473a2c7819f', base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')
model_name = 'qwen-plus'


async def gradio_func(message, history):
    print(f"history: {history}")
    transport = StreamableHttpTransport(url='http://127.0.0.1:8000/mcp')
    mcp_client = Client(transport)
    async with mcp_client:
        tools = await mcp_client.list_tools()
        tool_json_array = [tool.model_dump(exclude_none=True) for tool in tools]
        # print(f'tools: \n{tool_json_array}')
        prompt = system_prompt.replace("{{tools}}", json.dumps(tool_json_array))
        messages = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        # 添加历史对话
        messages += history
        messages.append({
            "role": "user",
            "content": message
        })
        
        answer = ""
        max_turns = 5
        for i in range(max_turns):
            response = await model_client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )
            model_output = ""
            if len(answer) > 0:
                answer += "\n"
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    model_output += content_chunk
                    answer += content_chunk
                    yield answer

            # model_output = response.choices[0].message.content
            print(f'turn_{i}: model output: {model_output}')
            final_answer_pattern = r"Final Answer:\s*(.*)"
            match = re.search(final_answer_pattern, model_output, re.DOTALL)
            if match:
                final_answer = match.group(1)
                break

            pattern = r"Action:\s*(\{.*\})"
            match = re.search(pattern, model_output, re.DOTALL)
            if match:
                action_str = match.group(1)
                action_json = json.loads(action_str)
                tool_result = await mcp_client.call_tool(action_json['tool_name'], action_json['arguments'])
                print('tool structed result: ', tool_result.structured_content)
                observation = tool_result.structured_content['result']
                answer += f"\nObservation：{observation}"
                yield answer
                model_output += f"\nObservation：{observation}"
            
            messages.append({
                "role": "assistant",
                "content": model_output 
            })
                



if __name__ == '__main__':
    gr.ChatInterface(fn=gradio_func, type='messages').queue().launch(inbrowser=True)