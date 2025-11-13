from flask import request, jsonify, current_app
from app.api import api_bp
from app.services.translator import translate_with_vocabulary
from app.services.document_generator import generate_word_document
import uuid
import os
import logging

from constants import MAX_TEXT_LENGTH

# 配置日志
logger = logging.getLogger(__name__)

@api_bp.route('/v1/translate', methods=['POST'])
def translate():
    """
    翻译文本API端点
    
    请求体参数:
    - text: 要翻译的英文文本
    - output_format: 输出格式，可选值为'json'或'word'，默认为'json'
    - include_vocabulary: 是否包含词汇表，默认为False
    
    返回:
    - 翻译结果，包括翻译文本、词汇表（如果请求）和Word文档URL（如果请求）
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要参数
        if not data or 'text' not in data:
            return jsonify({"success": False, "error": "缺少必要参数 'text'"}), 400
        
        # 获取参数，设置默认值
        text = data.get('text')
        output_format = data.get('output_format', 'json')
        include_vocabulary = data.get('include_vocabulary') == "true"
        
        # 限制文本长度
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({"success": False, "error": f"文本长度不能超过 {MAX_TEXT_LENGTH} 个字符"}), 400
        
        # 验证输出格式
        if output_format not in ['json', 'word']:
            return jsonify({"success": False, "error": "无效的输出格式，必须是 'json' 或 'word'"}), 400
        
        logger.info(f"接收到翻译请求，文本长度: {len(text)} 字符")
        
        # 执行翻译，如果需要则同时提取词汇表
        translation, vocabulary = translate_with_vocabulary(text, include_vocabulary)
        
        # 构建响应
        response = {
            "success": True,
            "translation": translation
        }
        
        # 如果需要词汇表，且成功提取了词汇
        if include_vocabulary and vocabulary:
            response["vocabulary"] = vocabulary
            logger.info(f"词汇提取完成，共提取 {len(vocabulary)} 个词汇")
        
        # 如果需要Word文档
        if output_format == 'word':
            logger.info("开始生成Word文档")
            # 生成唯一文件名
            file_id = str(uuid.uuid4())[:8]
            filename = f"translation_{file_id}.docx"
            filepath = os.path.join(current_app.config['DOWNLOAD_FOLDER'], filename)
            
            # 生成Word文档
            generate_word_document(text, translation, vocabulary, filepath)
            
            # 添加文档URL到响应
            response["word_document_url"] = f"/downloads/{filename}"
            logger.info(f"Word文档生成完成，文件名: {filename}")
        
        logger.info("翻译请求处理完成")
        return jsonify(response), 200
        
    except Exception as e:
        # 记录错误并返回错误响应
        logger.error(f"翻译请求处理错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500