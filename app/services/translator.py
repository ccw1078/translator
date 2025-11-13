import requests
import os
import logging
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL')

def get_translation_prompts(text, include_vocabulary):
    """
    根据是否需要词汇表生成相应的系统提示和用户提示
    
    参数:
    text (str): 要翻译的英文文本
    include_vocabulary (bool): 是否需要提取专业词汇
    
    返回:
    tuple: (system_prompt, user_prompt) - 系统提示和用户提示
    """
    if include_vocabulary:
        system_prompt = "You are a professional Chinese-English translation assistant who is also skilled at extracting technical terms."
        user_prompt = f"""Please complete the following tasks:
            1. Accurately translate the following English text into Chinese.
            2. Extract 3-5 of the most important technical terms or key concepts from both the English text and its translation.
            3. Return format: First provide the Chinese translation, then add the special marker '===Technical terms===', followed by a JSON-formatted list of the extracted terms.


            English Text:{text}

            Example of vocabulary in JSON format:
            [{{
                \"english\": \"Machine Learning\",
                \"chinese\": \"机器学习\",
                \"explanation\": \"计算机通过数据自动学习而不依赖明确编程的技术\"
            }}]
            Please strictly follow the above format when returning the result, and do not add any extra explanations"""
    else:
        system_prompt = "You are a professional Chinese-English translation assistant. Please accurately translate the English text provided by the user into Chinese. Return only the translation result, without adding any extra content."
        user_prompt = text
    
    return system_prompt, user_prompt


def get_payload(system_prompt, user_prompt):
    """
    构建DeepSeek API请求的payload
    
    参数:
    system_prompt (str): 系统提示
    user_prompt (str): 用户提示
    
    返回:
    dict: 符合DeepSeek API要求的payload格式
    """
    return {
        "model": "deepseek-chat",  # 使用DeepSeek对话模型
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # 降低温度以获得更确定性的结果
        "max_tokens": 3000  # 增加最大令牌数以支持词汇表
    }
    

def split_translation_vocabulary(content):
    """
    从翻译结果中分离中文翻译和专业词汇列表
    
    参数:
    content (str): 包含翻译和词汇表的完整响应内容，格式为"中文翻译===专业词汇===JSON格式的词汇表"
    
    返回:
    tuple: (translation, vocabulary_list)
        - translation (str): 提取的中文翻译内容
        - vocabulary_list (list): 解析后的专业词汇列表，每个词汇包含english、chinese和explanation字段
    """
    if '===专业词汇===' in content:
        parts = content.split('===专业词汇===')
        translation = parts[0].strip()
        vocabulary_json = parts[1].strip()
        
        # 尝试解析词汇表JSON
        try:
            vocabulary_list = json.loads(vocabulary_json)
            logger.info(f"翻译和词汇提取成功完成，共提取 {len(vocabulary_list)} 个专业术语")
            return translation, vocabulary_list
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试提取JSON部分
            logger.warning("词汇提取结果不是有效的JSON格式，尝试清理格式")
            start_idx = vocabulary_json.find('[')
            end_idx = vocabulary_json.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_json = vocabulary_json[start_idx:end_idx+1]
                try:
                    vocabulary_list = json.loads(cleaned_json)
                    logger.info(f"翻译和词汇提取成功完成，共提取 {len(vocabulary_list)} 个专业术语")
                    return translation, vocabulary_list
                except json.JSONDecodeError:
                    logger.error("清理后的词汇提取结果仍然不是有效的JSON格式")
                    return translation, [{"english": "Unknown", "chinese": "未知", "explanation": "词汇提取失败"}]
            else:
                logger.error("无法从响应中提取JSON格式的数据")
                return translation, [{"english": "Unknown", "chinese": "未知", "explanation": "词汇提取失败"}]
    else:
        # 如果没有找到词汇表标记，只返回翻译内容
        logger.warning("未在响应中找到词汇表部分")
        return content, []
    
def translate_with_vocabulary(text, include_vocabulary=False):
    """
    使用DeepSeek API将英文文本翻译为中文，并可选地提取专业词汇
    
    参数:
    text (str): 要翻译的英文文本
    include_vocabulary (bool): 是否同时提取专业词汇
    
    返回:
    tuple: (翻译后的中文文本, 词汇列表) 如果 include_vocabulary=True
           (翻译后的中文文本, []) 如果 include_vocabulary=False
    """
    try:
        # 验证API密钥
        if not DEEPSEEK_API_KEY:
            raise Exception("DeepSeek API密钥未配置")
        
        # 验证文本是否为空
        if not text.strip():
            return "输入文本不能为空", []
        
        # 获取翻译所需的prompt模板
        system_prompt, user_prompt = get_translation_prompts(text, include_vocabulary)
        
        # 构建请求数据
        payload = get_payload(system_prompt, user_prompt)
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        # 发送请求到DeepSeek API
        logger.info(f"发送翻译请求到DeepSeek API，文本长度: {len(text)} 字符, 包含词汇表: {include_vocabulary}")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        # 处理响应内容
        if include_vocabulary:
            return split_translation_vocabulary(content)
        else:
            # 只需要翻译结果
            logger.info("翻译成功完成")
            return content, []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API请求错误: {str(e)}")
        raise Exception(f"翻译服务请求失败: {str(e)}")
    except (KeyError, IndexError) as e:
        logger.error(f"DeepSeek API响应解析错误: {str(e)}")
        raise Exception(f"翻译服务响应格式错误: {str(e)}")
    except Exception as e:
        logger.error(f"翻译处理错误: {str(e)}")
        raise Exception(f"翻译服务处理失败: {str(e)}")

# 保持向后兼容
def translate_text(text):
    """
    使用DeepSeek API将英文文本翻译为中文（向后兼容函数）
    
    参数:
    text (str): 要翻译的英文文本
    
    返回:
    str: 翻译后的中文文本
    """
    translation, _ = translate_with_vocabulary(text, include_vocabulary=False)
    return translation