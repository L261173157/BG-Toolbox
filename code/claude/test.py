import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DouBao_API_KEY"), 
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
tools = [{
    "type": "web_search",
    "max_keyword": 4,
}]

# Enable tools
response = client.responses.create(
    model="deepseek-v3-1-terminus",
    input=[{"role": "user", "content": "北京的天气怎么样？"}],
    tools=tools,
)

print(response)