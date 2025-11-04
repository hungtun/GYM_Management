import os
import secrets
import cloudinary

class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:hwngt1412@127.0.0.1:3306/gym_db?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    PAGE_SIZE = 2


    def init_cloudinary():
        cloudinary.config(
            cloud_name="delrpa4vp",
            api_key="883465785855645",
            api_secret="2frClqJnhrVYWutKdfrXFaqTG6A",
        )
