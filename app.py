import os
import sys
import threading
import time
import random
from flask import Flask, render_template, request, jsonify, send_from_directory
from services import ServiceManager
from database import Database
from config import Config

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# 初始化数据库
db = Database(app.config['DATABASE_URI'])

# 全局服务管理器
service_manager = None

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PXE_FOLDER'], exist_ok=True)

# 检查是否是root权限
if os.geteuid() != 0:
    print("需要root权限运行DHCP和TFTP服务")
    print("请使用: sudo python3 app.py")
    sys.exit(1)

@app.route('/')
def index():
    """主页面路由"""
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """获取设备列表API"""
    devices = db.get_devices()
    return jsonify([{
        'id': d.id,
        'mac': d.mac,
        'status': d.status,
        'progress': d.progress,
        'image': d.image,
        'ip': d.ip,
        'last_seen': d.last_seen.timestamp() if d.last_seen else 0,
        'duration': d.duration
    } for d in devices])

@app.route('/api/services/status', methods=['GET'])
def get_services_status():
    """获取服务状态API"""
    global service_manager
    dhcp_running = service_manager.dhcp_running() if service_manager else False
    tftp_running = service_manager.tftp_running() if service_manager else False
    
    return jsonify({
        'dhcp': dhcp_running,
        'tftp': tftp_running,
        'system': {
            'cpu': random.randint(10, 30),
            'memory': random.randint(30, 60),
            'storage': random.randint(10, 40)
        }
    })

@app.route('/api/services/control', methods=['POST'])
def control_services():
    """控制服务API"""
    global service_manager
    data = request.json
    action = data.get('action')
    service = data.get('service', 'all')
    
    if service_manager is None:
        service_manager = ServiceManager()
    
    result = {'status': 'success'}
    
    try:
        if action == 'start':
            if service == 'dhcp' or service == 'all':
                if not service_manager.start_dhcp():
                    result['status'] = 'error'
                    result['message'] = 'DHCP服务启动失败或已在运行'
            if service == 'tftp' or service == 'all':
                if not service_manager.start_tftp():
                    result['status'] = 'error'
                    result['message'] = 'TFTP服务启动失败或已在运行'
        elif action == 'stop':
            if service == 'dhcp' or service == 'all':
                if not service_manager.stop_dhcp():
                    result['status'] = 'error'
                    result['message'] = 'DHCP服务停止失败或未运行'
            if service == 'tftp' or service == 'all':
                if not service_manager.stop_tftp():
                    result['status'] = 'error'
                    result['message'] = 'TFTP服务停止失败或未运行'
    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
    
    return jsonify(result)

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """文件上传API"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'config')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 保存文件到对应目录
    if file_type == 'image':
        save_path = os.path.join(app.config['PXE_FOLDER'], file.filename)
    else:
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    file.save(save_path)
    
    # 记录日志
    db.log_event(f"上传{file_type}文件: {file.filename}")
    
    return jsonify({
        'status': 'success',
        'filename': file.filename,
        'type': file_type,
        'size': os.path.getsize(save_path)
    })

@app.route('/api/files/list', methods=['GET'])
def list_files():
    """获取文件列表API"""
    config_files = []
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.endswith(('.cfg', '.conf', '.ini')):
            config_files.append({
                'name': f,
                'size': os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], f))
            })
    
    image_files = []
    for f in os.listdir(app.config['PXE_FOLDER']):
        if f.endswith(('.iso', '.img', '.gz')):
            image_files.append({
                'name': f,
                'size': os.path.getsize(os.path.join(app.config['PXE_FOLDER'], f))
            })
    
    return jsonify({
        'configs': config_files,
        'images': image_files
    })

@app.route('/api/system/logs', methods=['GET'])
def get_logs():
    """获取系统日志API"""
    logs = db.get_events(limit=10)
    return jsonify([{
        'id': l.id,
        'timestamp': l.timestamp.timestamp() if l.timestamp else 0,
        'message': l.message
    } for l in logs])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def device_monitor():
    """设备监控线程，模拟设备状态变化"""
    global service_manager
    while True:
        # 模拟设备状态变化
        devices = db.get_devices()
        for device in devices:
            if device.status == 'discovered':
                # 随机开始部署
                if random.random() < 0.3:  # 30%几率开始部署
                    db.update_device(device.id, status='deploying')
            elif device.status == 'deploying':
                # 随机增加进度
                progress_increment = random.randint(5, 15)
                new_progress = min(100, device.progress + progress_increment)
                db.update_device(device.id, progress=new_progress)
                
                if new_progress == 100:
                    # 随机决定成功或失败
                    status = 'success' if random.random() < 0.8 else 'failed'
                    db.update_device(device.id, status=status)
        
        # 随机添加新设备
        if len(devices) < 10 and service_manager and service_manager.dhcp_running():
            if random.random() < 0.2:  # 20%几率添加新设备
                db.add_device(
                    mac=f"{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}:{random.randint(0x00, 0xff):02X}",
                    status='discovered',
                    progress=0,
                    image=random.choice(['Ubuntu 22.04', 'Windows 10', 'CentOS 7', 'Debian 11']),
                    ip=f"192.168.1.{random.randint(100, 200)}",
                    duration=0
                )
        
        time.sleep(5)

if __name__ == '__main__':
    # 初始化数据库
    db.init_db()
    
    # 启动服务管理器
    service_manager = ServiceManager()
    
    # 启动设备监控线程
    monitor_thread = threading.Thread(target=device_monitor, daemon=True)
    monitor_thread.start()
    
    # 启动服务
    app.run(host='0.0.0.0', port=5000, debug=True)
