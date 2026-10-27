#!/bin/bash
INTERFACE=$1
if [ -z "$INTERFACE" ]; then echo "Usage: $0 <interface>"; exit 1; fi

tc qdisc add dev $INTERFACE root handle 1: htb default 40
tc class add dev $INTERFACE parent 1: classid 1:1 htb rate 1000mbit

tc class add dev $INTERFACE parent 1:1 classid 1:10 htb rate 200mbit ceil 1000mbit prio 1 # Exam
tc class add dev $INTERFACE parent 1:1 classid 1:20 htb rate 300mbit ceil 1000mbit prio 2 # ERP, Faculty
tc class add dev $INTERFACE parent 1:1 classid 1:30 htb rate 300mbit ceil 1000mbit prio 3 # IoT, CCTV
tc class add dev $INTERFACE parent 1:1 classid 1:40 htb rate 200mbit ceil 1000mbit prio 4 # Student

tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 match ip src 192.168.40.0/24 flowid 1:10
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 match ip src 192.168.30.0/24 flowid 1:20
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 2 u32 match ip src 192.168.20.0/24 flowid 1:20
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 3 u32 match ip src 192.168.50.0/24 flowid 1:30
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 3 u32 match ip src 192.168.60.0/24 flowid 1:30
tc filter add dev $INTERFACE protocol ip parent 1:0 prio 4 u32 match ip src 192.168.10.0/24 flowid 1:40
echo "QoS configured on $INTERFACE"
