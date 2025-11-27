from flask import request, jsonify, current_app, Response, stream_with_context
from app.api import api_bp
from app.services.translator import (
    translate_with_vocabulary,
    translate_with_vocabulary_stream,
)
from app.services.document_generator import generate_word_document
import uuid
import os
import logging
import json

from webargs import fields, validate
from webargs.flaskparser import use_args

from constants import MAX_TEXT_LENGTH

# 配置日志
logger = logging.getLogger(__name__)


def build_translation_response(
    translation, vocabulary, include_vocabulary, output_format, text
):
    """
    构建翻译响应

    参数:
    - translation: 翻译结果
    - vocabulary: 词汇表
    - include_vocabulary: 是否包含词汇表
    - output_format: 输出格式
    - text: 原始文本

    返回:
    - 翻译响应字典
    """
    # 构建基础响应
    response = {"success": True, "translation": translation}

    # 如果需要词汇表，且成功提取了词汇
    if include_vocabulary and vocabulary:
        response["vocabulary"] = vocabulary
        logger.info(f"词汇提取完成，共提取 {len(vocabulary)} 个词汇")

    # 如果需要Word文档
    if output_format == "word":
        logger.info("开始生成Word文档")
        # 生成唯一文件名
        file_id = str(uuid.uuid4())[:8]
        filename = f"translation_{file_id}.docx"
        filepath = os.path.join(current_app.config["DOWNLOAD_FOLDER"], filename)

        # 生成Word文档
        generate_word_document(text, translation, vocabulary, filepath)

        # 添加文档URL到响应
        response["word_document_url"] = f"/downloads/{filename}"
        logger.info(f"Word文档生成完成，文件名: {filename}")

    return response


translate_args = {
    # 要翻译的英文文本
    "text": fields.Str(
        required=True,
        validate=validate.Length(
            max=MAX_TEXT_LENGTH, error=f"文本长度不能超过 {MAX_TEXT_LENGTH} 个字符"
        ),
        error_messages={"required": "缺少必要参数 'text'"},
    ),
    # 输出格式，可选值为'json'或'word'，默认为'json'
    "output_format": fields.Str(
        load_default="json",
        validate=validate.OneOf(
            ["json", "word"], error="无效的输出格式，必须是 'json' 或 'word'"
        ),
    ),
    # 是否包含词汇表，默认为False
    "include_vocabulary": fields.Bool(load_default=False),
    # 是否启用流式响应，默认为False
    "streaming": fields.Bool(load_default=False),
}


@api_bp.route("/v1/translate", methods=["POST"])
@use_args(translate_args)
def translate(args):
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
        # 获取参数，设置默认值
        text = args.get("text")
        output_format = args.get("output_format", "json")
        include_vocabulary = args.get("include_vocabulary", False)

        logger.info(f"接收到翻译请求，文本长度: {len(text)} 字符")

        # 执行翻译，如果需要则同时提取词汇表
        translation, vocabulary = translate_with_vocabulary(text, include_vocabulary)

        # 构建响应
        response = build_translation_response(
            translation, vocabulary, include_vocabulary, output_format, text
        )

        logger.info("翻译请求处理完成")
        return jsonify(response), 200

    except Exception as e:
        # 记录错误并返回错误响应
        logger.error(f"翻译请求处理错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/v2/translate", methods=["POST"])
@use_args(translate_args)
def translate_stream(args):
    """
    翻译文本API端点（流式响应版本）

    请求体参数:
    - text: 要翻译的英文文本
    - include_vocabulary: 是否包含词汇表，默认为False

    返回:
    - 流式翻译结果
    """
    try:
        # 获取参数，设置默认值
        text = args.get("text")
        include_vocabulary = args.get("include_vocabulary", False)
        output_format = args.get("output_format", "json")

        # 检查是否请求了不支持的Word格式
        if output_format == "word":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"output_format": ["流式响应不支持Word文档格式"]},
                    }
                ),
                400,
            )

        logger.info(f"接收到流式翻译请求，文本长度: {len(text)} 字符")

        # 定义流式响应的生成器函数
        @stream_with_context
        def generate():
            try:
                # 用于存储完整的翻译结果
                full_translation = ""
                vocabulary_list = []

                # 调用流式翻译服务
                for chunk in translate_with_vocabulary_stream(text, include_vocabulary):
                    # 检查是否是最后一个chunk（包含完整结果）
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        full_translation, vocabulary_list = chunk
                        # 构建最终的词汇表JSON响应
                        response_data = {
                            "success": True,
                            "type": "complete",
                            "translation": full_translation,
                        }
                        if include_vocabulary and vocabulary_list:
                            response_data["vocabulary"] = vocabulary_list
                        yield f"data: {json.dumps(response_data)}\n\n"
                    else:
                        # 输出翻译的文本片段
                        if chunk:
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                # 结束信号
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"流式翻译请求处理错误: {str(e)}")
                yield f"data: {json.dumps({'success': False, 'type': 'error', 'error': str(e)})}\n\n"

        # 返回SSE格式的流式响应
        return Response(
            generate(),
            content_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        # 记录错误并返回错误响应
        logger.error(f"流式翻译请求处理错误: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
