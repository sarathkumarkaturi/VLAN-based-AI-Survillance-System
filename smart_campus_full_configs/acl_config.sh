#!/bin/bash
iptables -F
iptables -P FORWARD DROP
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Student (VLAN 10)
iptables -A FORWARD -s 192.168.10.0/24 -d 192.168.10.0/24 -j ACCEPT
iptables -A FORWARD -s 192.168.10.0/24 -d 192.168.30.0/24 -j DROP
iptables -A FORWARD -s 192.168.10.0/24 -d 192.168.40.0/24 -j DROP
iptables -A FORWARD -s 192.168.10.0/24 -j ACCEPT

# Faculty (VLAN 20)
iptables -A FORWARD -s 192.168.20.0/24 -d 192.168.30.0/24 -j ACCEPT
iptables -A FORWARD -s 192.168.20.0/24 -j ACCEPT

# IoT (VLAN 50)
iptables -A FORWARD -s 192.168.50.0/24 -d 192.168.20.0/24 -j DROP
iptables -A FORWARD -s 192.168.50.0/24 -j ACCEPT

# Others
iptables -A FORWARD -s 192.168.30.0/24 -j ACCEPT
iptables -A FORWARD -s 192.168.40.0/24 -j ACCEPT
iptables -A FORWARD -s 192.168.60.0/24 -j ACCEPT
echo "ACLs applied."
