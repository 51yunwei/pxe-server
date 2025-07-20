import os
import threading
import socketserver
from tftpy import TftpServer, TftpShared

class TFTPServer:
    def __init__(self, root='.'):
        self.root = os.path.abspath(root)
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        self.running = True
        # 重写TFTP处理程序以支持自定义根目录
        class CustomTftpHandler(TftpShared.TftpHandler):
            def get_file(self, path):
                return os.path.join(self.server.root, path)
        
        TftpShared.TftpHandler = CustomTftpHandler
        self.server = TftpServer.TftpServer(self.root)
        self.thread = threading.Thread(target=self.server.listen)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.stop()
        self.running = False
