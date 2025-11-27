import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入翻译函数，避免导入Flask应用
from app.services.translator import (
    translate_with_vocabulary,
    translate_with_vocabulary_stream,
    split_translation_vocabulary,
)


class TestTranslator(unittest.TestCase):

    @patch("app.services.translator.requests.post")
    def test_translate_text_success(self, mock_post):
        """测试翻译功能成功的情况"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好，世界！"}}]
        }
        mock_post.return_value = mock_response

        # 调用翻译函数
        translation, vocabulary = translate_with_vocabulary("Hello, world!")

        # 验证结果
        self.assertEqual(translation, "你好，世界！")
        self.assertEqual(vocabulary, [])
        mock_post.assert_called_once()

    @patch("app.services.translator.requests.post")
    def test_translate_text_api_error(self, mock_post):
        """测试API返回错误的情况"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        # 配置raise_for_status()方法抛出异常
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Bad Request"
        )
        mock_post.return_value = mock_response

        # 验证抛出异常
        with self.assertRaises(Exception):
            translate_with_vocabulary("Hello, world!")

    def test_translate_empty_text(self):
        """测试空文本的情况"""
        # 调用翻译函数（不需要模拟API，因为函数内部会处理空文本）
        translation, vocabulary = translate_with_vocabulary("")

        # 验证结果
        self.assertEqual(translation, "")
        self.assertEqual(vocabulary, [])

        # 测试只有空格的文本
        translation, vocabulary = translate_with_vocabulary("   ")
        self.assertEqual(translation, "")
        self.assertEqual(vocabulary, [])

    @patch("app.services.translator.requests.post")
    def test_translate_with_vocabulary(self, mock_post):
        """测试翻译并包含词汇表的情况"""
        # 设置模拟响应（包含词汇表部分）
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '机器学习是一种人工智能的应用。==Terms==[{"english": "Machine Learning", "chinese": "机器学习", "explanation": "计算机通过数据自动学习而不依赖明确编程的技术"}]'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # 调用翻译函数，包含词汇表
        translation, vocabulary = translate_with_vocabulary(
            "Machine Learning is an application of Artificial Intelligence.",
            include_vocabulary=True,
        )

        # 验证结果
        self.assertEqual(translation, "机器学习是一种人工智能的应用。")
        self.assertEqual(len(vocabulary), 1)
        self.assertEqual(vocabulary[0]["english"], "Machine Learning")
        self.assertEqual(vocabulary[0]["chinese"], "机器学习")
        self.assertIn("自动学习", vocabulary[0]["explanation"])
        mock_post.assert_called_once()

    @patch("app.services.translator.requests.post")
    def test_translate_with_vocabulary_stream(self, mock_post):
        """测试流式翻译功能"""
        # 设置模拟流式响应
        mock_response = MagicMock()
        mock_response.status_code = 200

        # 模拟流式响应的迭代器（使用英文文本避免bytes对象中的非ASCII字符问题）
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            b'data: {"choices": [{"delta": {"content": ", "}}]}',
            b'data: {"choices": [{"delta": {"content": "world"}}]}',
            b'data: {"choices": [{"delta": {"content": "!"}}]}',
            b"data: [DONE]",
        ]

        mock_post.return_value = mock_response

        # 调用流式翻译函数
        chunks = list(translate_with_vocabulary_stream("Hello, world!"))

        # 验证结果
        self.assertEqual(len(chunks), 2)  # 6个文本块 + 1个完成信号
        self.assertEqual(chunks[-1]["type"], "complete")
        self.assertTrue(chunks[-1]["done"])
        mock_post.assert_called_once()

    def test_split_translation_vocabulary(self):
        """测试分离翻译和词汇表功能的各种情况"""
        # 测试正常情况：包含有效词汇表
        content_with_vocab = '机器学习是一种人工智能的应用。==Terms==[{"english": "Machine Learning", "chinese": "机器学习", "explanation": "计算机通过数据自动学习而不依赖明确编程的技术"}]'
        translation, vocabulary = split_translation_vocabulary(content_with_vocab)
        self.assertEqual(translation, "机器学习是一种人工智能的应用。")
        self.assertEqual(len(vocabulary), 1)
        self.assertEqual(vocabulary[0]["english"], "Machine Learning")

        # 测试没有词汇表的情况
        content_without_vocab = "这是一个没有词汇表的翻译。"
        translation, vocabulary = split_translation_vocabulary(content_without_vocab)
        self.assertEqual(translation, "这是一个没有词汇表的翻译。")
        self.assertEqual(vocabulary, [])

        # 测试词汇表JSON格式有问题的情况（缺少右括号）
        content_bad_json = '测试文本。==Terms==[{"english": "Test", "chinese": "测试", "explanation": "这是一个测试"}'
        translation, vocabulary = split_translation_vocabulary(content_bad_json)
        self.assertEqual(translation, "测试文本。")
        self.assertEqual(len(vocabulary), 1)

        # 测试无法提取JSON的情况
        content_no_json = "测试文本。==Terms==无法提取JSON数据"
        translation, vocabulary = split_translation_vocabulary(content_no_json)
        self.assertEqual(translation, "测试文本。")
        self.assertEqual(len(vocabulary), 1)
        self.assertEqual(vocabulary[0]["english"], "Unknown")


if __name__ == "__main__":
    unittest.main()
