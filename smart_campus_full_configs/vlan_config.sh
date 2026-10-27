#!/bin/bash
# Open vSwitch VLAN Configuration
SWITCH_NAME=$1

if [ -z "$SWITCH_NAME" ]; then
    echo "Usage: $0 <switch_name>"
    exit 1
fi

run_ovs_cmd() {
    if eval "$1"; then
        echo "PASS: $1"
    else
        echo "FAIL: $1"
    fi
}

if [[ "$SWITCH_NAME" == dist_* ]]; then
    for i in {0..7}; do
        run_ovs_cmd "ovs-vsctl set port eth$i trunks=10,20,30,40,50,60"
    done
elif [[ "$SWITCH_NAME" == access_* ]]; then
    run_ovs_cmd "ovs-vsctl set port eth0 trunks=10,20,30,40,50,60"
    run_ovs_cmd "ovs-vsctl set port eth1 trunks=10,20,30,40,50,60"
    
    if [ "$SWITCH_NAME" == "access_student" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=10"
    elif [ "$SWITCH_NAME" == "access_faculty" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=20"
    elif [ "$SWITCH_NAME" == "access_erp" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=30"
    elif [ "$SWITCH_NAME" == "access_exam" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=40"
    elif [ "$SWITCH_NAME" == "access_iot" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=50"
    elif [ "$SWITCH_NAME" == "access_cctv" ]; then
        run_ovs_cmd "ovs-vsctl set port eth2 tag=60"
    fi
fi
echo "OVS config complete for $SWITCH_NAME."
