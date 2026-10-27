#!/bin/bash
# FRR Routing configuration
cat << 'EOF' > /etc/frr/frr.conf
frr defaults traditional
log syslog informational
no ipv6 forwarding
!
router ospf
 ospf router-id 1.1.1.1
 network 192.168.10.0/24 area 0
 network 192.168.20.0/24 area 0
 network 192.168.30.0/24 area 0
 network 192.168.40.0/24 area 0
 network 192.168.50.0/24 area 0
 network 192.168.60.0/24 area 0
!
EOF

for VLAN in 10 20 30 40 50 60; do
    ip link add link eth1 name eth1.$VLAN type vlan id $VLAN
    ip addr add 192.168.$VLAN.1/24 dev eth1.$VLAN
    ip link set eth1.$VLAN up
done
sysctl -w net.ipv4.ip_forward=1
echo "Routing configured."
