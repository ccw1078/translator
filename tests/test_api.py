import unittest
from unittest.mock import patch
import json
import sys
import os

from app.utils.helpers import generate_random_string
from constants import MAX_TEXT_LENGTH

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app


class TestAPI(unittest.TestCase):

    def setUp(self):
        """测试前设置"""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.testing = True

    @patch("app.api.routes.translate_with_vocabulary")
    def test_translate_api_basic(self, mock_translate_with_vocabulary):
        """测试基本翻译API功能"""
        # 设置模拟函数返回值
        mock_translate_with_vocabulary.return_value = ("你好，世界！", [])

        # 发送测试请求
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps({"text": "Hello, world!"}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["translation"], "你好，世界！")
        mock_translate_with_vocabulary.assert_called_once_with("Hello, world!", False)

    @patch("app.api.routes.translate_with_vocabulary")
    @patch("app.api.routes.generate_word_document")
    def test_translate_api_with_word_output(
        self, mock_generate, mock_translate_with_vocabulary
    ):
        """测试带Word输出的翻译API功能"""
        # 设置模拟函数返回值
        mock_translate_with_vocabulary.return_value = ("测试翻译", [])
        mock_generate.return_value = None

        # 发送测试请求
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps({"text": "Test translation", "output_format": "word"}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("word_document_url", data)

    def test_translate_api_missing_text(self):
        """测试缺少text参数的情况"""
        # 发送缺少text参数的请求
        response = self.client.post(
            "/api/v1/translate", data=json.dumps({}), content_type="application/json"
        )

        # 打印响应以调试
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data.decode('utf-8')}")

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("text", data["error"])

    def test_translate_api_invalid_format(self):
        """测试无效的output_format参数"""
        # 发送无效格式请求
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps({"text": "Test", "output_format": "invalid"}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("output_format", data["error"])

    def test_translate_api_text_too_long(self):
        """测试text参数过长的场景"""
        # 发送参数过长的请求
        text = generate_random_string(MAX_TEXT_LENGTH + 1)
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps(
                {
                    "text": text,
                }
            ),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("text", data["error"])

    @patch("app.api.routes.translate_with_vocabulary")
    def test_translate_api_with_vocabulary(self, mock_translate_with_vocabulary):
        """测试包含词汇表的翻译API功能"""
        # 设置模拟函数返回值
        mock_vocabulary = [
            {
                "english": "machine learning",
                "chinese": "机器学习",
                "explanation": "人工智能的一个分支",
            },
            {
                "english": "deep learning",
                "chinese": "深度学习",
                "explanation": "机器学习的一个子领域",
            },
        ]
        mock_translate_with_vocabulary.return_value = (
            "这是机器学习和深度学习的示例",
            mock_vocabulary,
        )

        # 发送测试请求
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps(
                {
                    "text": "This is an example of machine learning and deep learning",
                    "include_vocabulary": "true",
                }
            ),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["translation"], "这是机器学习和深度学习的示例")
        self.assertIn("vocabulary", data)
        self.assertEqual(len(data["vocabulary"]), 2)
        mock_translate_with_vocabulary.assert_called_once_with(
            "This is an example of machine learning and deep learning", True
        )

    @patch("app.api.routes.translate_with_vocabulary")
    @patch("app.api.routes.generate_word_document")
    def test_translate_api_with_vocabulary_and_word(
        self, mock_generate, mock_translate_with_vocabulary
    ):
        """测试同时包含词汇表和Word输出的翻译API功能"""
        # 设置模拟函数返回值
        mock_vocabulary = [
            {
                "english": "test",
                "chinese": "测试",
                "explanation": "验证功能正确性的过程",
            }
        ]
        mock_translate_with_vocabulary.return_value = ("这是一个测试", mock_vocabulary)
        mock_generate.return_value = None

        # 发送测试请求
        response = self.client.post(
            "/api/v1/translate",
            data=json.dumps(
                {
                    "text": "This is a test",
                    "include_vocabulary": "true",
                    "output_format": "word",
                }
            ),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("translation", data)
        self.assertIn("vocabulary", data)
        self.assertIn("word_document_url", data)

    @patch("app.api.routes.translate_with_vocabulary_stream")
    def test_translate_v2_api_basic(self, mock_translate_with_vocabulary_stream):
        """测试基本的/v2/translate流式API功能"""

        # 设置模拟函数返回值，模拟流式响应
        def mock_stream_response(text, include_vocabulary):
            chunks = ["你", "好", "，", "世", "界", "！"]
            for chunk in chunks:
                yield {"type": "chunk", "translation": chunk}
            # 最后返回完整结果
            yield {"type": "complete", "done": True}

        mock_translate_with_vocabulary_stream.side_effect = mock_stream_response

        # 发送测试请求
        response = self.client.post(
            "/api/v2/translate",
            data=json.dumps({"text": "Hello, world!"}),
            content_type="application/json",
        )

        # 验证响应状态和内容类型
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/event-stream")

        # 验证响应内容
        response_data = response.data.decode("utf-8")
        self.assertIn("chunk", response_data)
        self.assertIn("complete", response_data)
        self.assertIn("[DONE]", response_data)

    @patch("app.api.routes.translate_with_vocabulary_stream")
    def test_translate_v2_api_with_vocabulary(
        self, mock_translate_with_vocabulary_stream
    ):
        """测试包含词汇表的/v2/translate流式API功能"""

        # 设置模拟函数返回值
        def mock_stream_response(text, include_vocabulary):
            chunks = [
                "机",
                "器",
                "学",
                "习",
                "是",
                "人",
                "工",
                "智",
                "能",
                "的",
                "一",
                "个",
                "分",
                "支",
            ]
            for chunk in chunks:
                yield {"type": "chunk", "translation": chunk}
            # 最后返回完整结果和词汇表
            mock_vocabulary = [
                {
                    "english": "machine learning",
                    "chinese": "机器学习",
                    "explanation": "人工智能的一个分支",
                }
            ]
            yield {
                "type": "complete",
                "done": True,
                "translation": "机器学习是人工智能的一个分支",
                "vocabulary": mock_vocabulary,
            }

        mock_translate_with_vocabulary_stream.side_effect = mock_stream_response

        # 发送测试请求
        response = self.client.post(
            "/api/v2/translate",
            data=json.dumps(
                {
                    "text": "Machine learning is a branch of artificial intelligence",
                    "include_vocabulary": "true",
                }
            ),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        response_data = response.data.decode("utf-8")
        self.assertIn("chunk", response_data)
        self.assertIn("complete", response_data)
        self.assertIn("vocabulary", response_data)
        self.assertIn("[DONE]", response_data)

    def test_translate_v2_api_missing_text(self):
        """测试/v2/translate缺少text参数的情况"""
        # 发送缺少text参数的请求
        response = self.client.post(
            "/api/v2/translate", data=json.dumps({}), content_type="application/json"
        )

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("text", data["error"])

    def test_translate_v2_api_text_too_long(self):
        """测试/v2/translate文本长度超过限制的情况"""
        # 发送文本过长的请求
        text = generate_random_string(MAX_TEXT_LENGTH + 1)
        response = self.client.post(
            "/api/v2/translate",
            data=json.dumps({"text": text}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("text", data["error"])

    def test_translate_v2_api_word_format_not_supported(self):
        """测试/v2/translate使用不支持的word格式"""
        # 发送使用word格式的请求
        response = self.client.post(
            "/api/v2/translate",
            data=json.dumps({"text": "Hello, world!", "output_format": "word"}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("output_format", data["error"])

    @patch("app.api.routes.translate_with_vocabulary_stream")
    def test_translate_v2_api_service_error(
        self, mock_translate_with_vocabulary_stream
    ):
        """测试/v2/translate服务错误情况"""

        # 设置模拟函数抛出异常
        def mock_error_response(text, include_vocabulary):
            yield "翻译服务请求失败: API错误"

        mock_translate_with_vocabulary_stream.side_effect = mock_error_response

        # 发送测试请求
        response = self.client.post(
            "/api/v2/translate",
            data=json.dumps({"text": "Hello, world!"}),
            content_type="application/json",
        )

        # 验证响应
        self.assertEqual(response.status_code, 200)
        response_data = response.data.decode("utf-8")
        self.assertIn("[DONE]", response_data)


if __name__ == "__main__":
    unittest.main()
