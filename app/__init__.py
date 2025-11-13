from flask import Flask, send_from_directory
import os

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    app.config['DOWNLOAD_FOLDER'] = os.path.join(os.getcwd(), 'downloads')
    
    # 确保下载文件夹存在
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    # 注册蓝图
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # k8s 健康检查探针
    @app.route('/healthz', methods=['GET'])
    def health_check():
        """健康检查路由"""
        return "ok", 200
    
    # 静态文件路由
    @app.route('/downloads/<path:filename>')
    def download_file(filename):
        """提供下载文件的路由"""
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename)
    
    return app