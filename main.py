from app import create_app
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 获取端口配置，默认为5000
    port = int(os.environ.get('PORT', 5000))
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'True').lower() == 'true')