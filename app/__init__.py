from flask import Flask, send_from_directory, jsonify, abort
import os
from werkzeug.exceptions import HTTPException

# 配置webargs错误处理器
from webargs.flaskparser import parser as default_parser


@default_parser.error_handler
def handle_error(error, req, schema, **kwargs):
    """自定义错误处理器，返回与之前相同格式的JSON响应"""
    # 处理嵌套的错误信息结构
    if hasattr(error, "messages") and isinstance(error.messages, dict):
        # 获取所有错误信息的扁平结构
        all_errors = {}

        # 遍历所有位置（如'json'）的错误
        for location, location_errors in error.messages.items():
            if isinstance(location_errors, dict):
                for field, field_errors in location_errors.items():
                    if field not in all_errors:
                        all_errors[field] = []
                    all_errors[field].extend(field_errors)
            elif isinstance(location_errors, list):
                # 处理全局错误
                if "global" not in all_errors:
                    all_errors["global"] = []
                all_errors["global"].extend(location_errors)

    # 默认错误处理
    response = jsonify({"success": False, "error": all_errors})
    response.status_code = 400
    abort(response)


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)

    # 配置应用
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_secret_key")
    app.config["DOWNLOAD_FOLDER"] = os.path.join(os.getcwd(), "downloads")

    # 确保下载文件夹存在
    os.makedirs(app.config["DOWNLOAD_FOLDER"], exist_ok=True)

    # 注册蓝图
    from app.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # k8s 健康检查探针
    @app.route("/healthz", methods=["GET"])
    def health_check():
        """健康检查路由"""
        return "ok", 200

    # 静态文件路由
    @app.route("/downloads/<path:filename>")
    def download_file(filename):
        """提供下载文件的路由"""
        return send_from_directory(app.config["DOWNLOAD_FOLDER"], filename)

    return app
