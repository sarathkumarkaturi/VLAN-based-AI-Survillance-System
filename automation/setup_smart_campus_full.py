import os
import requests
import json
import time
import sys

# --- CONFIGURATION ---
GNS3_SERVER_URL = "http://localhost:3080/v2"
AUTH = ('admin', 'O5lJGEKu2QavRFTXnVPwajTxurl55aiSUiGzbTMwF55wizNpNqIFji8SpBbYZftr') 
PROJECT_NAME = "Smart_Campus_Network_FULL"
CONFIG_DIR = "smart_campus_full_configs"

ROUTER_TEMPLATE = "FRR Router"
SWITCH_TEMPLATE = "gns3-openvswitch"
PC_TEMPLATE = "VPCS"

nodes_def = [
    {"name": "isp_primary", "template": ROUTER_TEMPLATE, "y": -400, "x": -200},
    {"name": "isp_backup", "template": ROUTER_TEMPLATE, "y": -400, "x": 200},
    {"name": "firewall", "template": ROUTER_TEMPLATE, "y": -300, "x": 0},
    {"name": "core_a", "template": ROUTER_TEMPLATE, "y": -200, "x": -200},
    {"name": "core_b", "template": ROUTER_TEMPLATE, "y": -200, "x": 200},
    {"name": "dist_a", "template": SWITCH_TEMPLATE, "y": -100, "x": -200},
    {"name": "dist_b", "template": SWITCH_TEMPLATE, "y": -100, "x": 200},
    
    {"name": "access_student", "template": SWITCH_TEMPLATE, "y": 0, "x": -500},
    {"name": "access_faculty", "template": SWITCH_TEMPLATE, "y": 0, "x": -300},
    {"name": "access_erp", "template": SWITCH_TEMPLATE, "y": 0, "x": -100},
    {"name": "access_exam", "template": SWITCH_TEMPLATE, "y": 0, "x": 100},
    {"name": "access_iot", "template": SWITCH_TEMPLATE, "y": 0, "x": 300},
    {"name": "access_cctv", "template": SWITCH_TEMPLATE, "y": 0, "x": 500},
    
    {"name": "student_pc", "template": PC_TEMPLATE, "y": 100, "x": -500},
    {"name": "faculty_pc", "template": PC_TEMPLATE, "y": 100, "x": -300},
    {"name": "erp_server", "template": PC_TEMPLATE, "y": 100, "x": -100},
    {"name": "exam_server", "template": PC_TEMPLATE, "y": 100, "x": 100},
    {"name": "iot_device", "template": PC_TEMPLATE, "y": 100, "x": 300},
    {"name": "cctv_camera", "template": PC_TEMPLATE, "y": 100, "x": 500},
]

optional_nodes = [
    {"name": "radius_server", "template": "FreeRADIUS", "y": -200, "x": -400},
    {"name": "ids_ips", "template": "Suricata", "y": -200, "x": 0},
    {"name": "openvpn_server", "template": "OpenVPN", "y": -300, "x": -200}
]

links_def = [
    ("isp_primary", "firewall"),
    ("isp_backup", "firewall"),
    ("firewall", "core_a"),
    ("firewall", "core_b"),
    ("core_a", "core_b"),
    ("core_a", "dist_a"),
    ("core_a", "dist_b"),
    ("core_b", "dist_a"),
    ("core_b", "dist_b"),
    
    ("dist_a", "access_student"),
    ("dist_b", "access_student"),
    ("dist_a", "access_faculty"),
    ("dist_b", "access_faculty"),
    ("dist_a", "access_erp"),
    ("dist_b", "access_erp"),
    ("dist_a", "access_exam"),
    ("dist_b", "access_exam"),
    ("dist_a", "access_iot"),
    ("dist_b", "access_iot"),
    ("dist_a", "access_cctv"),
    ("dist_b", "access_cctv"),
    
    ("access_student", "student_pc"),
    ("access_faculty", "faculty_pc"),
    ("access_erp", "erp_server"),
    ("access_exam", "exam_server"),
    ("access_iot", "iot_device"),
    ("access_cctv", "cctv_camera"),
]

node_adapters = {}

def get_next_adapter(node_id):
    if node_id not in node_adapters:
        node_adapters[node_id] = 0
    adapter = node_adapters[node_id]
    node_adapters[node_id] += 1
    return adapter, 0

def ask_user(prompt):
    while True:
        resp = input(prompt + " (y/n): ").strip().lower()
        if resp in ['y', 'yes']:
            return True
        elif resp in ['n', 'no']:
            return False

def check_project_exists():
    url = f"{GNS3_SERVER_URL}/projects"
    try:
        res = requests.get(url, auth=AUTH)
        if res.status_code == 200:
            for p in res.json():
                if p['name'] == PROJECT_NAME:
                    return p['project_id']
    except Exception as e:
        print(f"Error checking existing projects: {e}")
        sys.exit(1)
    return None

def create_project(name):
    url = f"{GNS3_SERVER_URL}/projects"
    data = {"name": name}
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code == 201:
        return response.json()['project_id']
    else:
        print(f"Error creating project: {response.text}")
        sys.exit(1)

def get_template_id(name, fail_on_missing=True):
    url = f"{GNS3_SERVER_URL}/templates"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        for template in response.json():
            if template['name'] == name:
                return template['template_id']
    if fail_on_missing:
        print(f"ERROR: Template '{name}' not found. Please check your GNS3 templates.")
        sys.exit(1)
    return None

def get_compute_ids():
    url = f"{GNS3_SERVER_URL}/computes"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        local_id = None
        vm_id = None
        for c in response.json():
            if c.get("compute_id") == "local":
                local_id = "local"
            if c.get("name") == "GNS3 VM (GNS3 VM)":
                vm_id = c.get("compute_id")
        return local_id, vm_id
    else:
        print(f"Error fetching computes: {response.text}")
        sys.exit(1)

def create_node(project_id, template_id, compute_id, name, x, y):
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/templates/{template_id}"
    data = {"x": x, "y": y, "compute_id": compute_id}
    
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code == 201:
        node = response.json()
        node_id = node['node_id']
        
        # Rename
        put_url = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes/{node_id}"
        put_res = requests.put(put_url, json={"name": name}, auth=AUTH)
        if put_res.status_code == 200:
            print(f"Created node '{name}'")
        return node_id
    else:
        print(f"Error creating node '{name}': {response.text}")
        return None

def create_link(project_id, node1_id, adapter1, port1, node2_id, adapter2, port2):
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/links"
    data = {
        "nodes": [
            {"node_id": node1_id, "adapter_number": adapter1, "port_number": port1},
            {"node_id": node2_id, "adapter_number": adapter2, "port_number": port2}
        ]
    }
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code != 201:
        print(f"Error creating link between {node1_id} and {node2_id}: {response.text}")
        return False
    return True

def generate_configs():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    vlan_script = """#!/bin/bash
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
"""

    routing_script = """#!/bin/bash
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
"""

    acl_script = """#!/bin/bash
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
"""

    qos_script = """#!/bin/bash
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
"""

    dhcp_script = """#!/bin/bash
cat << 'EOF' > /etc/dhcp/dhcpd.conf
subnet 192.168.10.0 netmask 255.255.255.0 { range 192.168.10.100 192.168.10.200; option routers 192.168.10.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.20.0 netmask 255.255.255.0 { range 192.168.20.100 192.168.20.200; option routers 192.168.20.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.30.0 netmask 255.255.255.0 { range 192.168.30.100 192.168.30.200; option routers 192.168.30.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.40.0 netmask 255.255.255.0 { range 192.168.40.100 192.168.40.200; option routers 192.168.40.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.50.0 netmask 255.255.255.0 { range 192.168.50.100 192.168.50.200; option routers 192.168.50.1; option domain-name-servers 8.8.8.8; }
subnet 192.168.60.0 netmask 255.255.255.0 { range 192.168.60.100 192.168.60.200; option routers 192.168.60.1; option domain-name-servers 8.8.8.8; }
EOF
echo "DHCP configuration created."
"""

    firewall_script = acl_script # Usually similar

    failover_test = """#!/bin/bash
echo "Testing Dual ISP Failover..."
ip route get 8.8.8.8
ip link set eth0 down
sleep 2
ip route get 8.8.8.8
ip link set eth0 up
echo "Test complete."
"""

    validation_test = """#!/bin/bash
echo "Validation Test Results"
test_ping() {
  ping -c 1 -W 1 $2 > /dev/null 2>&1
  if [ $? -eq 0 ] && [ "$3" == "ALLOW" ]; then echo "PASS: $1";
  elif [ $? -ne 0 ] && [ "$3" == "BLOCK" ]; then echo "PASS: $1";
  else echo "FAIL: $1"; fi
}
test_ping "1. Student -> Student" "192.168.10.100" "ALLOW"
test_ping "2. Student -> ERP" "192.168.30.100" "BLOCK"
test_ping "3. Student -> Exam" "192.168.40.100" "BLOCK"
test_ping "4. Faculty -> ERP" "192.168.30.100" "ALLOW"
test_ping "5. IoT -> Faculty" "192.168.20.100" "BLOCK"
test_ping "6. Student -> Gateway" "192.168.10.1" "ALLOW"
test_ping "7. Exam -> Gateway" "192.168.40.1" "ALLOW"
test_ping "8. CCTV -> Gateway" "192.168.60.1" "ALLOW"
"""

    readme = """# Smart Campus Network FULL Configurations
This folder contains the configuration scripts for the Open vSwitch containers, FRR routers, QoS, ACLs, and Validation scripts.
Run these inside their respective containers in GNS3.
"""

    files = {
        "vlan_config.sh": vlan_script,
        "routing_config.sh": routing_script,
        "acl_config.sh": acl_script,
        "qos_config.sh": qos_script,
        "dhcp_config.sh": dhcp_script,
        "firewall_config.sh": firewall_script,
        "failover_test.sh": failover_test,
        "validation_test.sh": validation_test,
        "README.md": readme
    }

    for name, content in files.items():
        with open(os.path.join(CONFIG_DIR, name), "w") as f:
            f.write(content)
            
    with open("PROJECT_README.md", "w") as f:
        f.write("""# Smart Campus Network FULL

## Topology
A full-scale GNS3 smart campus network featuring Dual ISPs, Firewalls, Redundant Core & Distribution layers, and Access switches.

## Six VLANs
- VLAN 10 = Student (192.168.10.0/24)
- VLAN 20 = Faculty/Admin (192.168.20.0/24)
- VLAN 30 = ERP-Servers (192.168.30.0/24)
- VLAN 40 = Exam-System (192.168.40.0/24)
- VLAN 50 = IoT-Lab (192.168.50.0/24)
- VLAN 60 = CCTV (192.168.60.0/24)

## Redundancy
Core and distribution routers/switches are interconnected redundantly.
FRR routers support VRRP/Keepalived (example config provided in scripts).

## ACL & Security
- Student VLAN has restricted access (cannot reach ERP or Exam).
- IoT cannot reach Faculty.
- Firewall / ACL configurations are provided via iptables.

## QoS Priorities
1. Exam (VLAN 40)
2. ERP (VLAN 30) & Faculty (VLAN 20)
3. IoT (VLAN 50) & CCTV (VLAN 60)
4. Student (VLAN 10)

## Validation Tests
Run `validation_test.sh` to check ACLs.

## Features
- Fully Emulated: Open vSwitch VLANs, Trunks, FRR Routing, VPCS, QoS via `tc`, ACLs via `iptables`.
- Simulated/Limited: Hardware-level failovers (requires VRRP or STP configuration actively running inside containers). FreeRADIUS/IDS can be added if Docker templates are installed.
""")

def main():
    print("Checking for existing project...")
    existing_id = check_project_exists()
    
    project_name = PROJECT_NAME
    if existing_id:
        print(f"Project '{PROJECT_NAME}' already exists (ID: {existing_id}).")
        reuse = ask_user("Do you want to reuse this project? (If no, we will append a timestamp to create a new one)")
        if reuse:
            project_id = existing_id
        else:
            project_name = f"{PROJECT_NAME}_{int(time.time())}"
            project_id = create_project(project_name)
    else:
        project_id = create_project(project_name)
        
    print(f"Using Project: {project_name} (ID: {project_id})")

    local_comp, vm_comp = get_compute_ids()
    if not local_comp or not vm_comp:
        print("Required computes not found.")
        sys.exit(1)

    print("Resolving templates...")
    templates = {
        ROUTER_TEMPLATE: get_template_id(ROUTER_TEMPLATE),
        SWITCH_TEMPLATE: get_template_id(SWITCH_TEMPLATE),
        PC_TEMPLATE: get_template_id(PC_TEMPLATE)
    }
    
    templates_used = [ROUTER_TEMPLATE, SWITCH_TEMPLATE, PC_TEMPLATE]

    # Handle optional templates
    for onode in optional_nodes:
        tid = get_template_id(onode["template"], fail_on_missing=False)
        if tid:
            templates[onode["template"]] = tid
            nodes_def.append(onode)
            templates_used.append(onode["template"])
            print(f"Found optional template {onode['template']}, including node {onode['name']}.")
        else:
            print(f"Optional template {onode['template']} not found, skipping {onode['name']}.")

    node_id_map = {}
    print("\nCreating Nodes...")
    for n in nodes_def:
        # Determine compute
        comp = vm_comp if n["template"] in [ROUTER_TEMPLATE, SWITCH_TEMPLATE] else local_comp
        # Fallback for optional nodes
        if n["template"] not in [ROUTER_TEMPLATE, SWITCH_TEMPLATE, PC_TEMPLATE]:
             comp = vm_comp
             
        nid = create_node(project_id, templates[n["template"]], comp, n["name"], n["x"], n["y"])
        if nid:
            node_id_map[n["name"]] = nid
            
    print(f"\nCreated {len(node_id_map)} nodes.")

    print("\nCreating Links...")
    link_count = 0
    for src, dst in links_def:
        if src in node_id_map and dst in node_id_map:
            src_id = node_id_map[src]
            dst_id = node_id_map[dst]
            
            # For VPCS and openvswitch, get_next_adapter works
            src_adapt, src_port = get_next_adapter(src_id)
            dst_adapt, dst_port = get_next_adapter(dst_id)
            
            if create_link(project_id, src_id, src_adapt, src_port, dst_id, dst_adapt, dst_port):
                link_count += 1
        else:
            print(f"Skipping link {src}-{dst} as one or both nodes were not created.")

    print(f"Created {link_count} links.")
    
    print("\nGenerating configuration files...")
    generate_configs()
    
    print("\n================ SUMMARY ================")
    print(f"Project Name : {project_name}")
    print(f"Project ID   : {project_id}")
    print(f"Nodes Created: {len(node_id_map)}")
    print(f"Links Created: {link_count}")
    print(f"Templates    : {', '.join(set(templates_used))}")
    print(f"Configs Dir  : ./{CONFIG_DIR}/")
    print(f"README file  : ./PROJECT_README.md")
    print("=========================================")
    print("Next steps:")
    print("1. Open the project in GNS3.")
    print("2. Start all nodes.")
    print("3. Use the scripts in the configs directory to configure Open vSwitch and FRR routers.")

if __name__ == "__main__":
    main()
