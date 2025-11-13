import os

is_dev = os.getenv("FLASK_ENV") == 'development'

bind = '0.0.0.0:5000'
workers = 3 # 此处需要留意 k8s 的资源配额限制，否则会出现 OOM 问题，两个 worker 使用大约 80M 内存
reload = is_dev
loglevel = 'debug' if is_dev else 'warning'
log_file = "-"
max_requests = 100
max_requests_jitter = 50
timeout = 240
worker_class = 'gevent'
