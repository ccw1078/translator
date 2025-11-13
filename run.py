from gevent import monkey
monkey.patch_all()

from main import app
import logging

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.info")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run(host="0.0.0.0")