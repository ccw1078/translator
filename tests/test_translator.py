import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.translator import translate_text

class TestTranslator(unittest.TestCase):
    
    @patch('app.services.translator.requests.post')
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
        result = translate_text("Hello, world!")
        
        # 验证结果
        self.assertEqual(result, "你好，世界！")
        mock_post.assert_called_once()
    
    @patch('app.services.translator.requests.post')
    def test_translate_text_api_error(self, mock_post):
        """测试API返回错误的情况"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        # 关键修改：配置raise_for_status()方法抛出异常
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
        mock_post.return_value = mock_response
        
        # 验证抛出异常
        with self.assertRaises(Exception):
            translate_text("Hello, world!")
    
    def test_translate_empty_text(self):
        """测试空文本的情况"""
        result = translate_text("")
        self.assertEqual(result, "输入文本不能为空")

if __name__ == '__main__':
    unittest.main()