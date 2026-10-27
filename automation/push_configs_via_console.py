import requests
import socket
import time
import sys

# --- CONFIGURATION ---
GNS3_SERVER_URL = "http://localhost:3080/v2"
AUTH = ('admin', 'O5lJGEKu2QavRFTXnVPwajTxurl55aiSUiGzbTMwF55wizNpNqIFji8SpBbYZftr') # Set to None if GNS3 doesn't require authentication
PROJECT_NAME = "Smart_Campus_Network"

def get_project_id(name):
    url = f"{GNS3_SERVER_URL}/projects"
    try:
        response = requests.get(url, auth=AUTH)
        if response.status_code == 200:
            for p in response.json():
                if p['name'] == name:
                    return p['project_id']
    except Exception as e:
        print(f"Error connecting to GNS3 API: {e}")
    return None

def get_nodes(project_id):
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        return response.json()
    return []

def send_commands_via_console(host, port, commands):
    print(f"Connecting to console at {host}:{port}...")
    try:
        # Create socket connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        
        # Press enter a few times to wake up the console
        s.send(b"\r\n\r\n")
        time.sleep(1)
        
        # Read the banner/prompt
        s.recv(4096)
        
        for cmd in commands:
            if not cmd.strip() and cmd != "":
                continue
            
            s.send(f"{cmd}\r\n".encode('ascii'))
            time.sleep(0.1) # Small delay between commands to prevent buffering issues
            
            # For longer commands or saving config, wait a bit longer
            if "write memory" in cmd or "crypto" in cmd:
                time.sleep(2)
                
        print(f"Configuration pushed successfully to {host}:{port}")
        s.close()
    except Exception as e:
        print(f"Failed to connect or send commands to {host}:{port}. Error: {e}")

def main():
    print(f"Looking for project: {PROJECT_NAME}")
    project_id = get_project_id(PROJECT_NAME)
    
    if not project_id:
        print(f"Project '{PROJECT_NAME}' not found. Did you run setup_gns3_topology.py first?")
        sys.exit(1)
        
    print(f"Found project ID: {project_id}")
    nodes = get_nodes(project_id)
    
    # Read the configs we generated earlier
    try:
        with open("core_switch_config.txt", "r") as f:
            core_config = f.read().splitlines()
        with open("access_switch_config.txt", "r") as f:
            access_config = f.read().splitlines()
    except FileNotFoundError:
        print("Configuration files not found. Please run generate_configs.py first.")
        sys.exit(1)
        
    # Iterate through nodes and push configs based on their names
    for node in nodes:
        name = node.get("name", "")
        console_port = node.get("console")
        console_host = node.get("console_host", "127.0.0.1")
        status = node.get("status")
        
        if status != "started":
            print(f"Skipping {name} because it is not running (Status: {status}). Please start the nodes in GNS3 first.")
            continue
            
        if not console_port:
            print(f"Skipping {name} because it has no console port.")
            continue
            
        print(f"\n--- Configuring {name} ---")
        
        if "Core" in name:
            # We customize the hostname based on the node name
            custom_core_config = [cmd if not cmd.startswith("hostname") else f"hostname {name}" for cmd in core_config]
            send_commands_via_console(console_host, console_port, custom_core_config)
            
        elif "Distribution" in name:
            # Distribution acts similarly to core in terms of VLAN passing but no routing
            # For simplicity in this simulation, we'll push a basic L2 config
            dist_config = [
                "enable", "configure terminal", f"hostname {name}",
                "vtp mode transparent", "vlan 10,20,30,40,50,60", "exit",
                "interface range GigabitEthernet0/1-3", 
                "switchport trunk encapsulation dot1q", "switchport mode trunk", "no shutdown",
                "end", "write memory"
            ]
            send_commands_via_console(console_host, console_port, dist_config)
            
        elif "Access" in name:
            custom_access_config = [cmd if not cmd.startswith("hostname") else f"hostname {name}" for cmd in access_config]
            
            # Map VLANs depending on the access switch name based on the PDF design
            vlan_id = "10"
            if "Exam" in name: vlan_id = "40"
            elif "CCTV" in name: vlan_id = "60"
            
            # Replace the generic vlan 10 access port assignment with the specific one
            custom_access_config = [cmd.replace("switchport access vlan 10", f"switchport access vlan {vlan_id}") for cmd in custom_access_config]
            
            send_commands_via_console(console_host, console_port, custom_access_config)
        else:
            print(f"Skipping {name}, no automated config defined for this device type.")

if __name__ == "__main__":
    main()
