from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入路由处理函数
from app.api.routes import *