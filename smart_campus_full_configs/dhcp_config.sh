#!/bin/bash
cat << 'EOF' > /etc/dhcp/dhcpd.conf
subnet 192.168.10.0 netmask 255.255.255.0 { range 192.168.10.100 192.168.10.200; option routers 192.168.10.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.20.0 netmask 255.255.255.0 { range 192.168.20.100 192.168.20.200; option routers 192.168.20.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.30.0 netmask 255.255.255.0 { range 192.168.30.100 192.168.30.200; option routers 192.168.30.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.40.0 netmask 255.255.255.0 { range 192.168.40.100 192.168.40.200; option routers 192.168.40.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.50.0 netmask 255.255.255.0 { range 192.168.50.100 192.168.50.200; option routers 192.168.50.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.60.0 netmask 255.255.255.0 { range 192.168.60.100 192.168.60.200; option routers 192.168.60.1; option domain-name-servers 8.8.8.8; }
EOF
echo "DHCP configuration created."
