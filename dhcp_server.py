import socket
from scapy.all import *
from database import add_device, update_device_status

class DHCPServer:
    def __init__(self, interface='eth0', ip_pool='192.168.1.100-192.168.1.200'):
        self.interface = interface
        self.ip_start, self.ip_end = ip_pool.split('-')
        self.running = False
        self.sock = None
        self.leases = {}

    def start(self):
        self.running = True
        self.sock = conf.L2socket(iface=self.interface)
        sniff(filter="udp and (port 67 or 68)", 
              prn=self.handle_dhcp, 
              stop_filter=lambda x: not self.running)

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

    def handle_dhcp(self, packet):
        if DHCP in packet and packet[DHCP].options[0][1] == 1:  # DHCP Discover
            self.process_discover(packet)
        elif DHCP in packet and packet[DHCP].options[0][1] == 3:  # DHCP Request
            self.process_request(packet)

    def process_discover(self, packet):
        mac = packet[Ether].src
        client_ip = self.get_available_ip(mac)
        
        offer = Ether(dst=mac)/IP(src=self.ip_start[:-3], dst=client_ip)
        offer /= UDP(sport=67, dport=68)/BOOTP(op=2, yiaddr=client_ip, xid=packet[BOOTP].xid)
        offer /= DHCP(options=[("message-type", "offer"),
                              ("server_id", self.ip_start[:-3]),
                              ("subnet_mask", "255.255.255.0"),
                              ("router", self.ip_start[:-3]),
                              ("lease_time", 3600),
                              "end"])
        
        self.sock.send(offer)
        add_device(mac, 'Discover', 10)

    def process_request(self, packet):
        mac = packet[Ether].src
        client_ip = self.get_available_ip(mac)
        
        ack = Ether(dst=mac)/IP(src=self.ip_start[:-3], dst=client_ip)
        ack /= UDP(sport=67, dport=68)/BOOTP(op=2, yiaddr=client_ip, xid=packet[BOOTP].xid)
        ack /= DHCP(options=[("message-type", "ack"),
                            ("server_id", self.ip_start[:-3]),
                            ("subnet_mask", "255.255.255.0"),
                            ("router", self.ip_start[:-3]),
                            ("tftp_server", self.ip_start[:-3]),
                            ("bootfile_name", "pxelinux.0"),
                            "end"])
        
        self.sock.send(ack)
        update_device_status(mac, 'Ack', 50)
        self.leases[mac] = client_ip

    def get_available_ip(self, mac):
        if mac in self.leases:
            return self.leases[mac]
        
        # 简化IP分配逻辑
        return self.ip_start
