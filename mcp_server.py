# 安装依赖
# pip install fastmcp
from fastmcp import FastMCP

# 初始化 FastMCP
mcp = FastMCP()

# 加法
@mcp.tool(title="整数加法")
def add_tool(a: int, b: int):
    """返回两个整数的加法结果"""
    return {"result": a + b}

# 减法
@mcp.tool(title="整数减法")
def sub_tool(a: int, b: int):
    """返回两个整数的减法结果"""
    return {"result": a - b}

# 乘法
@mcp.tool(title="整数乘法")
def mul_tool(a: int, b: int):
    """返回两个整数的乘法结果"""
    return {"result": a * b}

# 除法
@mcp.tool(title="整数除法")
def div_tool(a: int, b: int):
    """返回两个整数的除法结果，如果除数为0则提示错误"""
    if b == 0:
        return {"result": "错误：除数不能为0"}
    return {"result": a / b}

# 启动服务
if __name__ == "__main__":
    mcp.run(transport='streamable-http')
