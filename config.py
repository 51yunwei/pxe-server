# config.py
import os

class Config:
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pxe-server-secret-key'
    
    # 文件路径配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PXE_FOLDER = os.path.join(BASE_DIR, 'pxe')
    
    # 数据库配置
    DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'pxe.db')
    
    # 服务配置
    DHCP_INTERFACE = 'eth0'
    DHCP_IP_POOL = '192.168.1.100-192.168.1.200'
