import threading
import os
import time
import socket
import struct
import random
from tftpy import TftpServer

class DHCPServer:
    def __init__(self, interface='eth0', ip_pool='192.168.1.100-192.168.1.200'):
        self.interface = interface
        self.ip_start, self.ip_end = ip_pool.split('-')
        self.running = False
        self.thread = None
        self.sock = None
        self.server_ip = self.get_server_ip(ip_pool)
        self.leases = {}
        print(f"DHCP服务器初始化: 接口={interface}, IP池={ip_pool}, 服务器IP={self.server_ip}")

    def get_server_ip(self, ip_pool):
        """从IP池中提取服务器IP（通常是池中的第一个IP）"""
        start_ip = ip_pool.split('-')[0]
        parts = start_ip.split('.')
        parts[-1] = '1'  # 通常服务器IP是.1
        return '.'.join(parts)

    def start(self):
        if self.running:
            print("DHCP服务已在运行中")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("DHCP服务已启动")
        return True

    def _run(self):
        """DHCP服务器主循环"""
        try:
            # 创建UDP套接字并绑定到端口67
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 设置超时以便定期检查运行状态
            self.sock.settimeout(1)
            
            # 绑定到所有接口的67端口
            self.sock.bind(('0.0.0.0', 67))
            print("DHCP服务正在监听端口 67...")
            
            while self.running:
                try:
                    # 接收DHCP数据包
                    data, addr = self.sock.recvfrom(1024)
                    mac = self.extract_mac(data)
                    
                    if mac:
                        print(f"收到来自 {mac} 的DHCP请求")
                        # 分配IP地址
                        client_ip = self.assign_ip(mac)
                        # 发送DHCP Offer
                        self.send_dhcp_offer(mac, client_ip)
                except socket.timeout:
                    # 超时是正常的，继续循环检查运行状态
                    continue
                except Exception as e:
                    if self.running:  # 仅在服务运行时打印错误
                        print(f"DHCP处理错误: {e}")
                    continue
        except Exception as e:
            print(f"DHCP服务运行错误: {e}")
        finally:
            if self.sock:
                self.sock.close()
                self.sock = None
            print("DHCP服务主循环退出")

    def extract_mac(self, data):
        """从DHCP数据包中提取MAC地址"""
        if len(data) < 28:
            return None
            
        # MAC地址在数据包偏移28字节处
        mac = data[28:34]
        return ':'.join(f"{b:02x}" for b in mac).upper()

    def assign_ip(self, mac):
        """为客户端分配IP地址"""
        if mac in self.leases:
            return self.leases[mac]
        
        # 简单分配策略：使用池中第一个IP
        client_ip = self.ip_start
        self.leases[mac] = client_ip
        print(f"为 {mac} 分配IP: {client_ip}")
        return client_ip

    def send_dhcp_offer(self, mac, client_ip):
        """发送DHCP Offer响应"""
        sock = None
        try:
            # 创建UDP套接字发送响应
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('0.0.0.0', 68))
            
            # 构建简化的DHCP Offer数据包
            # 注意: 这是一个简化实现，实际DHCP协议更复杂
            offer = bytes([
                0x02,  # BOOTP reply
                0x01, 0x06, 0x00, 0x00,  # htype, hlen, hops, xid
                0x00, 0x00, 0x00, 0x00,  # secs, flags
                *[int(part) for part in client_ip.split('.')],  # yiaddr
                *[int(part) for part in self.server_ip.split('.')],  # siaddr
                0x00, 0x00, 0x00, 0x00,  # giaddr
                *[int(part, 16) for part in mac.split(':')],  # chaddr
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # chaddr padding
                *([0]*192),  # sname and file (填充0)
                0x63, 0x82, 0x53, 0x63,  # magic cookie: DHCP
                0x35, 0x01, 0x02,        # DHCP Message Type: Offer
                0x01, 0x04, 0xFF, 0xFF, 0xFF, 0x00,  # Subnet Mask: 255.255.255.0
                0x03, 0x04, *[int(part) for part in self.server_ip.split('.')],  # Router
                0x06, 0x04, *[int(part) for part in self.server_ip.split('.')],  # DNS Server
                0x33, 0x04, 0x00, 0x00, 0x0E, 0x10,  # Lease Time: 3600 seconds
                0x36, 0x04, *[int(part) for part in self.server_ip.split('.')],  # DHCP Server Identifier
                0xFF  # End
            ])
            
            # 发送广播响应
            sock.sendto(offer, ('255.255.255.255', 68))
            print(f"已向 {mac} 发送DHCP Offer, IP: {client_ip}")
        except Exception as e:
            print(f"发送DHCP Offer失败: {e}")
        finally:
            if sock:
                sock.close()

    def stop(self):
        if not self.running:
            print("DHCP服务已停止或未运行")
            return False
            
        print("正在停止DHCP服务...")
        self.running = False
        
        # 关闭套接字以中断recvfrom
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"关闭DHCP套接字时出错: {e}")
            finally:
                self.sock = None
        
        # 等待线程结束
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=2.0)
                if self.thread.is_alive():
                    print("警告: DHCP线程未在超时时间内终止")
            except Exception as e:
                print(f"等待DHCP线程结束时出错: {e}")
        
        print("DHCP服务已停止")
        return True

    def is_running(self):
        return self.running

class TFTPServer:
    def __init__(self, root='.'):
        self.root = os.path.abspath(root)
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        if self.running:
            print("TFTP服务已在运行中")
            return False
            
        self.running = True
        self.server = TftpServer(self.root)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("TFTP服务已启动")
        return True

    def _run(self):
        try:
            print("TFTP服务正在启动...")
            self.server.listen('0.0.0.0', 69)
            print("TFTP服务正在监听端口 69...")
        except Exception as e:
            print(f"TFTP服务启动失败: {e}")
            self.running = False
        finally:
            # 服务停止后清理
            if not self.running:
                self.server = None

    def stop(self):
        if not self.running:
            print("TFTP服务已停止或未运行")
            return False
            
        print("正在停止TFTP服务...")
        self.running = False
        
        if self.server:
            try:
                self.server.stop()
                print("TFTP服务已停止")
            except Exception as e:
                print(f"停止TFTP服务时出错: {e}")
        
        # 等待线程结束
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=2.0)
                if self.thread.is_alive():
                    print("警告: TFTP线程未在超时时间内终止")
            except Exception as e:
                print(f"等待TFTP线程结束时出错: {e}")
        
        return True

    def is_running(self):
        return self.running

class ServiceManager:
    def __init__(self):
        self.dhcp_server = DHCPServer()
        self.tftp_server = TFTPServer(root='pxe')
        # 使用简单的布尔值属性
        self._dhcp_running = False
        self._tftp_running = False

    def start_dhcp(self):
        if self._dhcp_running:
            print("DHCP服务已在运行中")
            return False
            
        try:
            success = self.dhcp_server.start()
            if success:
                self._dhcp_running = True
            return success
        except Exception as e:
            print(f"启动DHCP服务时出错: {e}")
            return False

    def stop_dhcp(self):
        if not self._dhcp_running:
            print("DHCP服务未运行")
            return False
            
        try:
            success = self.dhcp_server.stop()
            if success:
                self._dhcp_running = False
            return success
        except Exception as e:
            print(f"停止DHCP服务时出错: {e}")
            return False

    def start_tftp(self):
        if self._tftp_running:
            print("TFTP服务已在运行中")
            return False
            
        try:
            success = self.tftp_server.start()
            if success:
                self._tftp_running = True
            return success
        except Exception as e:
            print(f"启动TFTP服务时出错: {e}")
            return False

    def stop_tftp(self):
        if not self._tftp_running:
            print("TFTP服务未运行")
            return False
            
        try:
            success = self.tftp_server.stop()
            if success:
                self._tftp_running = False
            return success
        except Exception as e:
            print(f"停止TFTP服务时出错: {e}")
            return False

    def dhcp_running(self):
        return self._dhcp_running
    
    def tftp_running(self):
        return self._tftp_running
