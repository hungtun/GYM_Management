import os
import secrets
import cloudinary

class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:123456@localhost:3306/gym_db?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    PAGE_SIZE = 2

    # Email SMTP Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'quockhanh.qkdd@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'shgq xjaz owfd hvew')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'GYM Beta <quockhanh.qkdd@gmail.com>')

    def init_cloudinary():
        cloudinary.config(
            cloud_name="delrpa4vp",
            api_key="883465785855645",
            api_secret="2frClqJnhrVYWutKdfrXFaqTG6A",
        )
