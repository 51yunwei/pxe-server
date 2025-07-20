// 页面导航功能
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        // 更新活动导航链接
        document.querySelectorAll('.nav-link').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // 显示对应页面
        const targetPage = this.getAttribute('data-page');
        document.querySelectorAll('.page-content').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(targetPage).classList.add('active');
        
        // 加载特定页面数据
        switch(targetPage) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'devices':
                loadAllDevices();
                break;
            case 'control':
                loadServiceStatus();
                loadServiceLogs();
                break;
            case 'files':
                loadFileLists();
                break;
        }
    });
});

// 加载仪表盘数据
function loadDashboardData() {
    fetch('/api/services/status')
        .then(response => response.json())
        .then(data => {
            updateServiceStatus(data);
            updateSystemStatus(data.system);
        });
    
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            updateActiveDevices(data);
            updateDeviceCounts(data);
        });
}

// 加载所有设备
function loadAllDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            renderAllDevices(data);
        });
}

// 加载服务状态
function loadServiceStatus() {
    fetch('/api/services/status')
        .then(response => response.json())
        .then(data => {
            updateControlPanelStatus(data);
        });
}

// 加载服务日志
function loadServiceLogs() {
    fetch('/api/system/logs')
        .then(response => response.json())
        .then(logs => {
            renderServiceLogs(logs);
        });
}

// 加载文件列表
function loadFileLists() {
    fetch('/api/files/list')
        .then(response => response.json())
        .then(data => {
            renderFileLists(data);
        });
}

// 更新服务状态
function updateServiceStatus(status) {
    // 更新指示器
    const dhcpIndicator = document.getElementById('dhcp-indicator');
    const tftpIndicator = document.getElementById('tftp-indicator');
    
    dhcpIndicator.className = status.dhcp ? 'service-indicator service-on' : 'service-indicator service-off';
    tftpIndicator.className = status.tftp ? 'service-indicator service-on' : 'service-indicator service-off';
    
    // 更新状态文本
    document.getElementById('dhcp-status').textContent = status.dhcp ? '运行中 - 已分配32个IP' : '已停止';
    document.getElementById('tftp-status').textContent = status.tftp ? '运行中 - 已传输18.7GB' : '已停止';
    
    // 更新进度条
    document.getElementById('dhcp-progress').style.width = status.dhcp ? '65%' : '0%';
    document.getElementById('tftp-progress').style.width = status.tftp ? '45%' : '0%';
    
    // 更新控制按钮
    const dhcpBtn = document.getElementById('dhcp-control');
    const tftpBtn = document.getElementById('tftp-control');
    const allBtn = document.getElementById('all-services-control');
    
    if (status.dhcp) {
        dhcpBtn.innerHTML = '<i class="fas fa-stop me-1"></i>停止服务';
        dhcpBtn.className = 'btn btn-outline-danger btn-sm';
    } else {
        dhcpBtn.innerHTML = '<i class="fas fa-play me-1"></i>启动服务';
        dhcpBtn.className = 'btn btn-outline-success btn-sm';
    }
    
    if (status.tftp) {
        tftpBtn.innerHTML = '<i class="fas fa-stop me-1"></i>停止服务';
        tftpBtn.className = 'btn btn-outline-danger btn-sm';
    } else {
        tftpBtn.innerHTML = '<i class="fas fa-play me-1"></i>启动服务';
        tftpBtn.className = 'btn btn-outline-success btn-sm';
    }
    
    if (status.dhcp || status.tftp) {
        allBtn.innerHTML = '<i class="fas fa-power-off me-2"></i>停止所有服务';
        allBtn.className = 'btn btn-pxe btn-pxe-stop';
    } else {
        allBtn.innerHTML = '<i class="fas fa-power-off me-2"></i>启动所有服务';
        allBtn.className = 'btn btn-pxe';
    }
    
    // 更新页脚状态
    const footerDhcpIndicator = document.getElementById('footer-dhcp-indicator');
    const footerTftpIndicator = document.getElementById('footer-tftp-indicator');
    
    footerDhcpIndicator.className = status.dhcp ? 'service-indicator service-on me-2' : 'service-indicator service-off me-2';
    footerTftpIndicator.className = status.tftp ? 'service-indicator service-on me-2' : 'service-indicator service-off me-2';
    
    document.getElementById('footer-dhcp-status').textContent = status.dhcp ? '运行中' : '已停止';
    document.getElementById('footer-tftp-status').textContent = status.tftp ? '运行中' : '已停止';
}

// 更新系统状态
function updateSystemStatus(system) {
    document.getElementById('cpu-usage').textContent = `${system.cpu}%`;
    document.getElementById('memory-usage').textContent = `${system.memory}%`;
    document.getElementById('storage-usage').textContent = `${system.storage}%`;
    
    // 更新页脚
    document.getElementById('footer-cpu').textContent = `${system.cpu}%`;
    document.getElementById('footer-memory').textContent = `${system.memory}%`;
    document.getElementById('footer-storage').textContent = `${system.storage}%`;
}

// 更新活动设备
function updateActiveDevices(devices) {
    const container = document.getElementById('active-devices');
    container.innerHTML = '';
    
    // 只显示状态为 discovered 或 deploying 的设备
    const activeDevices = devices.filter(d => d.status === 'discovered' || d.status === 'deploying');
    
    activeDevices.forEach(device => {
        const row = document.createElement('tr');
        row.className = 'device-row';
        
        // 状态徽章类
        let badgeClass = '';
        if (device.status === 'discovered') badgeClass = 'bg-discovered';
        else if (device.status === 'deploying') badgeClass = 'bg-deploying';
        else if (device.status === 'success') badgeClass = 'bg-success';
        else if (device.status === 'failed') badgeClass = 'bg-failed';
        
        // 进度条类
        let progressClass = '';
        if (device.status === 'deploying') progressClass = 'bg-info';
        else if (device.status === 'success') progressClass = 'bg-success';
        else if (device.status === 'failed') progressClass = 'bg-danger';
        
        row.innerHTML = `
            <td class="device-mac">${device.mac}</td>
            <td>
                <span class="status-badge ${badgeClass}">${getStatusText(device.status)}</span>
            </td>
            <td>
                <div class="progress">
                    <div class="progress-bar ${progressClass}" role="progressbar" 
                         style="width: ${device.progress}%" 
                         aria-valuenow="${device.progress}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
            </td>
            <td>${device.image}</td>
            <td>${device.ip}</td>
            <td class="last-seen">${device.duration}分钟</td>
            <td>
                <button class="btn btn-sm btn-outline-${device.status === 'deploying' ? 'danger' : 'primary'} action-btn">
                    <i class="fas fa-${device.status === 'deploying' ? 'stop' : 'play'}"></i>
                </button>
            </td>
        `;
        container.appendChild(row);
    });
}

// 更新设备数量统计
function updateDeviceCounts(devices) {
    const total = devices.length;
    const success = devices.filter(d => d.status === 'success').length;
    const failed = devices.filter(d => d.status === 'failed').length;
    const deploying = devices.filter(d => d.status === 'deploying').length;
    const discovered = devices.filter(d => d.status === 'discovered').length;
    
    document.getElementById('device-count').textContent = total;
    document.getElementById('success-count').textContent = success;
    document.getElementById('failed-count').textContent = failed;
    document.getElementById('deploying-count').textContent = deploying + discovered;
}

// 渲染所有设备
function renderAllDevices(devices) {
    const container = document.getElementById('all-devices');
    container.innerHTML = '';
    
    devices.forEach(device => {
        const row = document.createElement('tr');
        row.className = 'device-row';
        
        // 状态徽章类
        let badgeClass = '';
        if (device.status === 'discovered') badgeClass = 'bg-discovered';
        else if (device.status === 'deploying') badgeClass = 'bg-deploying';
        else if (device.status === 'success') badgeClass = 'bg-success';
        else if (device.status === 'failed') badgeClass = 'bg-failed';
        
        // 进度条类
        let progressClass = '';
        if (device.status === 'deploying') progressClass = 'bg-info';
        else if (device.status === 'success') progressClass = 'bg-success';
        else if (device.status === 'failed') progressClass = 'bg-danger';
        
        // 格式化最后活跃时间
        const now = Date.now() / 1000;
        const lastSeen = device.last_seen;
        const diffMinutes = Math.floor((now - lastSeen) / 60);
        
        row.innerHTML = `
            <td class="device-mac">${device.mac}</td>
            <td>
                <span class="status-badge ${badgeClass}">${getStatusText(device.status)}</span>
            </td>
            <td>
                <div class="progress">
                    <div class="progress-bar ${progressClass}" role="progressbar" 
                         style="width: ${device.progress}%" 
                         aria-valuenow="${device.progress}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
            </td>
            <td>${device.image}</td>
            <td class="last-seen">${diffMinutes}分钟前</td>
            <td>
                <button class="btn btn-sm btn-outline-primary action-btn">
                    <i class="fas fa-redo"></i>
                </button>
            </td>
        `;
        container.appendChild(row);
    });
}

// 更新控制面板状态
function updateControlPanelStatus(status) {
    const dhcpIndicator = document.getElementById('control-dhcp-indicator');
    const tftpIndicator = document.getElementById('control-tftp-indicator');
    
    dhcpIndicator.className = status.dhcp ? 'service-indicator service-on' : 'service-indicator service-off';
    tftpIndicator.className = status.tftp ? 'service-indicator service-on' : 'service-indicator service-off';
    
    const dhcpBtn = document.getElementById('control-dhcp-btn');
    const tftpBtn = document.getElementById('control-tftp-btn');
    const allBtn = document.getElementById('control-all-btn');
    
    // 修复按钮状态逻辑
    if (status.dhcp) {
        dhcpBtn.innerHTML = '<i class="fas fa-stop me-1"></i> 停止服务';
        dhcpBtn.className = 'btn btn-pxe-stop me-2';
    } else {
        dhcpBtn.innerHTML = '<i class="fas fa-play me-1"></i> 启动服务';
        dhcpBtn.className = 'btn btn-success me-2';
    }
    
    if (status.tftp) {
        tftpBtn.innerHTML = '<i class="fas fa-stop me-1"></i> 停止服务';
        tftpBtn.className = 'btn btn-pxe-stop me-2';
    } else {
        tftpBtn.innerHTML = '<i class="fas fa-play me-1"></i> 启动服务';
        tftpBtn.className = 'btn btn-success me-2';
    }
    
    // 修复所有服务按钮状态
    if (status.dhcp || status.tftp) {
        allBtn.innerHTML = '<i class="fas fa-power-off me-2"></i>停止所有PXE服务';
        allBtn.className = 'btn btn-pxe btn-pxe-stop';
    } else {
        allBtn.innerHTML = '<i class="fas fa-power-off me-2"></i>启动所有PXE服务';
        allBtn.className = 'btn btn-pxe';
    }
}

// 渲染服务日志
function renderServiceLogs(logs) {
    const container = document.getElementById('service-logs');
    container.innerHTML = '';
    
    logs.forEach(log => {
        const timestamp = new Date(log.timestamp * 1000).toLocaleString();
        const alert = document.createElement('div');
        alert.className = 'alert alert-info p-2 mb-2';
        
        const message = document.createElement('small');
        message.textContent = `${timestamp} | ${log.message}`;
        
        alert.appendChild(message);
        container.appendChild(alert);
    });
}

// 渲染文件列表
function renderFileLists(files) {
    // 配置文件列表
    const configList = document.getElementById('config-file-list');
    configList.innerHTML = '';
    
    files.configs.forEach(file => {
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        item.innerHTML = `
            ${file.name}
            <div>
                <button class="btn btn-sm btn-outline-primary me-1">
                    <i class="fas fa-download"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        configList.appendChild(item);
    });
    
    // 镜像文件列表
    const imageList = document.getElementById('image-file-list');
    imageList.innerHTML = '';
    
    files.images.forEach(file => {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
        
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        item.innerHTML = `
            ${file.name}
            <span class="badge bg-light text-dark">${sizeMB} MB</span>
        `;
        imageList.appendChild(item);
    });
}

// 获取状态文本
function getStatusText(status) {
    switch(status) {
        case 'discovered': return '已发现';
        case 'deploying': return '部署中';
        case 'success': return '成功';
        case 'failed': return '失败';
        default: return status;
    }
}

// 服务控制按钮事件
document.getElementById('control-dhcp-btn').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('dhcp', action);
});

document.getElementById('control-tftp-btn').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('tftp', action);
});

document.getElementById('control-all-btn').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('all', action);
});

// 控制台服务按钮事件
document.getElementById('dhcp-control').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('dhcp', action);
});

document.getElementById('tftp-control').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('tftp', action);
});

document.getElementById('all-services-control').addEventListener('click', function() {
    const action = this.innerHTML.includes('停止') ? 'stop' : 'start';
    confirmServiceAction('all', action);
});

// 确认服务操作
function confirmServiceAction(service, action) {
    const serviceNames = {
        'dhcp': 'DHCP服务',
        'tftp': 'TFTP服务',
        'all': '所有服务'
    };
    
    const actionText = action === 'start' ? '启动' : '停止';
    const serviceName = serviceNames[service];
    
    const confirmation = confirm(`确定要${actionText}${serviceName}吗？`);
    
    if (confirmation) {
        controlService(service, action);
    }
}

// 控制服务
function controlService(service, action) {
    fetch('/api/services/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            service: service,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 更新UI
            loadServiceStatus();
            
            // 记录日志
            const event = `${action === 'start' ? '启动' : '停止'}${service === 'all' ? '所有服务' : service.toUpperCase()}服务`;
            fetch('/api/system/logs')
                .then(response => response.json())
                .then(logs => {
                    renderServiceLogs(logs);
                });
        } else {
            alert(`操作失败: ${data.message || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('控制服务时出错:', error);
        alert('控制服务时发生错误');
    });
}

// 文件上传处理
document.getElementById('configFile').addEventListener('change', function(e) {
    uploadFile(this.files[0], 'config');
});

document.getElementById('imageFile').addEventListener('change', function(e) {
    uploadFile(this.files[0], 'image');
});

function uploadFile(file, type) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    
    fetch('/api/files/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 更新文件列表
            loadFileLists();
            
            // 显示上传成功消息
            const areaId = type === 'config' ? 'configUploadArea' : 'imageUploadArea';
            const icon = type === 'config' ? 'fa-file-code' : 'fa-file-archive';
            
            document.getElementById(areaId).innerHTML = `
                <div class="text-success">
                    <i class="fas fa-check-circle fa-3x mb-2"></i>
                    <h5>${data.filename}</h5>
                    <p class="mb-0">${(data.size / (1024*1024)).toFixed(2)} MB</p>
                    <p>${type === 'config' ? '配置文件' : '系统镜像'}上传成功</p>
                </div>
            `;
        }
    });
}

// 刷新按钮事件
document.getElementById('refresh-devices').addEventListener('click', loadDashboardData);
document.getElementById('refresh-all-devices').addEventListener('click', loadAllDevices);

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    // 加载初始数据
    loadDashboardData();
    
    // 设置定时刷新
    setInterval(loadDashboardData, 5000);
    setInterval(loadServiceLogs, 10000);
});
