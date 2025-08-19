# calculator_agent.py
import openai

system_prompt = """
### 角色
你是一个通用智能代理。

### 任务
你的任务是解答用户问题，你需要逐步思考，在必要时调用工具。

### 思考步骤
你必须按照以下格式回答：
Thought: 解释你要做的推理
Action: 调用某个工具，例如 add_tool(12, 7)
Observation: 工具返回的结果
...（可多轮）
Final Answer: 最终结果

### 工具列表
{{tools}}

"""

client = openai.OpenAI(api_key='sk-e259258120804170b6809473a2c7819f', base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')


import asyncio
from fastmcp import FastMCP, Client
import json

async def main():
    # 连接 MCP 服务
    async with Client("http://localhost:8000/mcp") as client:
        # 获取工具列表
        tools = await client.list_tools()
        tool_array = [tool.model_dump() for tool in tools]
        print("已发现的工具:", json.dumps(tool_array, ensure_ascii=False, indent=4))
        system_prompt = system_prompt.replace('{{tools}}', json.dumps(tool_array, ensure_ascii=False, indent=4))
        system_prompt + "\n用户问题: " + "计算1 + 3 * 5 * 4" + "\n"

        for turn in range(max_turns):
            # 调用 LLM 生成推理 + 行动
            response = client.ChatCompletion.create(
                model="qwen3-32b",  # 或其他模型
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1
            )
            llm_output = response['choices'][0]['message']['content']
            print(llm_output)

            # 执行工具调用
            obs = None
            if "add_tool" in llm_output:
                a, b = map(int, llm_output.split("add_tool(")[1].split(")")[0].split(","))
                obs = add_tool(a, b)["result"]
            elif "sub_tool" in llm_output:
                a, b = map(int, llm_output.split("sub_tool(")[1].split(")")[0].split(","))
                obs = sub_tool(a, b)["result"]
            elif "mul_tool" in llm_output:
                a, b = map(int, llm_output.split("mul_tool(")[1].split(")")[0].split(","))
                obs = mul_tool(a, b)["result"]
            elif "div_tool" in llm_output:
                a, b = map(int, llm_output.split("div_tool(")[1].split(")")[0].split(","))
                obs = div_tool(a, b)["result"]

            # 将 Observation 反馈给 LLM
            if obs is not None:
                prompt += llm_output + f"\nObservation: {obs}\n"

            # 检查是否完成
            if "Final Answer" in llm_output:
                break
        

if __name__ == '__main__':
    asyncio.run(main())