#!/bin/bash
echo "Testing Dual ISP Failover..."
ip route get 8.8.8.8
ip link set eth0 down
sleep 2
ip route get 8.8.8.8
ip link set eth0 up
echo "Test complete."
