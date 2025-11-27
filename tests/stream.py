#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import sys


API_URL = "http://localhost:5000/api/v2/translate"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}

PAYLOAD = {
    "text": (
        "This year, as millions of families in the US sit down to celebrate Thanksgiving, "
        'many will tuck into one of the most quintessentially "American" foods: macaroni and cheese. '
    ),
    "output_format": "word",
    "include_vocabulary": True,
    "streaming": True,
}
# ===============================================


def test_streaming_api():
    print("🚀 正在发送流式请求...\n")

    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=PAYLOAD,
            stream=True,  # 关键：启用流式响应
            timeout=30,  # 可根据需要调整
        )
        response.raise_for_status()  # 检查 HTTP 错误

        print("📡 开始接收流式响应（实时输出）：\n")

        # 逐块读取响应内容（以换行符或 chunk 边界分割）
        for chunk in response.iter_lines():
            if chunk:
                try:
                    # 尝试解析为 JSON（适用于 JSONL 或 SSE 中的 data: {...}）
                    decoded = chunk.decode("utf-8")

                    # 如果是 SSE 格式（如 "data: {...}"），提取 data 部分
                    if decoded.startswith("data:"):
                        json_str = decoded[5:].strip()
                        if json_str == "[DONE]":
                            print("\n✅ 流结束标记收到。")
                            break
                        data = json.loads(json_str)
                    else:
                        # 否则尝试直接解析整行为 JSON
                        data = json.loads(decoded)

                    # 美化打印 JSON
                    print(json.dumps(data, indent=2, ensure_ascii=False))

                except json.JSONDecodeError:
                    # 非 JSON 内容（如纯文本流）直接打印
                    print(decoded)

    except requests.exceptions.Timeout:
        print("❌ 请求超时", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断请求。")
    except Exception as e:
        print(f"💥 未知错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    test_streaming_api()
