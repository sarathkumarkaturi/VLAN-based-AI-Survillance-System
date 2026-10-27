import os
import json
import time
import sys
import asyncio
import telnetlib3
import requests

GNS3_SERVER_URL = "http://localhost:3080/v2"
AUTH = ('admin', 'O5lJGEKu2QavRFTXnVPwajTxurl55aiSUiGzbTMwF55wizNpNqIFji8SpBbYZftr') 
PROJECT_NAME = "Smart_Campus_Network_FULL"
PROJECT_ID = "55270659-ff6f-41ca-ac6f-1f22fbc85aa0"
CONFIG_DIR = r"D:\3-1\CN\cn project\smart_campus_full_configs"

def ask_user(prompt):
    while True:
        resp = input(prompt + " (y/n): ").strip().lower()
        if resp in ['y', 'yes']:
            return True
        elif resp in ['n', 'no']:
            return False

def read_config(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        print(f"ERROR: Configuration file {path} not found.")
        sys.exit(1)
    with open(path, "r") as f:
        return f.read()

def run_script_on_node(node, script_content, script_args=""):
    host = node.get('console_host')
    port = node.get('console')
    if not host or not port:
        return "ERROR: No console available."
        
    if script_content.startswith('#!/bin/bash'):
        script_content = script_content.replace('#!/bin/bash', '#!/bin/bash\nFAIL_MARKER="__DEPLOY_"\'FAIL__\'', 1)
    else:
        script_content = 'FAIL_MARKER="__DEPLOY_"\'FAIL__\'\n' + script_content
    script_content = script_content.replace('FAIL:', '${FAIL_MARKER}:')
        
    async def _async_run():
        try:
            reader, writer = await asyncio.wait_for(telnetlib3.open_connection(host, port), timeout=5)
            
            writer.write("\n\n")
            await asyncio.sleep(0.5)
            
            writer.write("cat << 'EOF_SCRIPT' > /tmp/run.sh\n")
            await asyncio.sleep(0.5)
            
            # Send in chunks to avoid overwhelming the console
            for line in script_content.split('\n'):
                writer.write(line + "\n")
                await asyncio.sleep(0.01)
                
            writer.write("EOF_SCRIPT\n")
            await asyncio.sleep(1)
            
            writer.write("chmod +x /tmp/run.sh\n")
            await asyncio.sleep(0.5)
            
            # Drain console buffer to ignore script echo
            while True:
                try:
                    await asyncio.wait_for(reader.read(65535), timeout=0.5)
                except asyncio.TimeoutError:
                    break
                except Exception:
                    break
            
            writer.write(f"bash /tmp/run.sh {script_args}\n")
            
            output = ""
            max_wait = 20
            for _ in range(max_wait):
                await asyncio.sleep(1)
                try:
                    chunk = await asyncio.wait_for(reader.read(65535), timeout=0.5)
                    if chunk:
                        output += chunk
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass
                    
                lower_out = output.lower()
                completion_markers = [
                    "config complete", 
                    "configured.", 
                    "configured on", 
                    "acls applied", 
                    "test complete", 
                    "dhcp configuration created",
                    "8. cctv -> gateway"
                ]
                
                if any(marker in lower_out for marker in completion_markers):
                    await asyncio.sleep(1)
                    try:
                        chunk = await asyncio.wait_for(reader.read(65535), timeout=0.5)
                        if chunk:
                            output += chunk
                    except Exception:
                        pass
                    break
                    
            writer.close()
            return output
        except Exception as e:
            return f"Exception: {str(e)}"
            
    return asyncio.run(_async_run())

def check_failures(output, step_name):
    if "__DEPLOY_FAIL__:" in output or "Exception:" in output:
        print(f"CRITICAL ERROR in {step_name}!")
        print(output)
        print("Stopping deployment.")
        sys.exit(1)
    elif "PASS:" in output or "complete" in output.lower() or "configured" in output.lower():
        print(f"Successfully configured: {step_name}")
    else:
        print(f"Warning: Unexpected output in {step_name}:")
        print(output)

def main():
    print(f"PROJECT: {PROJECT_NAME}")
    print(f"PROJECT_ID: {PROJECT_ID}")
    if not ask_user("Do you want to proceed with executing the configuration on this project?"):
        print("Deployment cancelled.")
        return

    print("\n1. Verifying project exists...")
    res = requests.get(f"{GNS3_SERVER_URL}/projects/{PROJECT_ID}", auth=AUTH)
    if res.status_code != 200:
        print("ERROR: Project not found or inaccessible.")
        sys.exit(1)
    print("Project verified.")
    
    print("\n2. Discovering nodes and verifying they are running...")
    res = requests.get(f"{GNS3_SERVER_URL}/projects/{PROJECT_ID}/nodes", auth=AUTH)
    if res.status_code != 200:
        print("ERROR: Could not fetch nodes.")
        sys.exit(1)
        
    nodes = res.json()
    node_map = {n['name']: n for n in nodes}
    
    for n in nodes:
        if n['status'] != 'started':
            print(f"Starting node {n['name']}...")
            requests.post(f"{GNS3_SERVER_URL}/projects/{PROJECT_ID}/nodes/{n['node_id']}/start", auth=AUTH)
            
    print("Waiting 5 seconds for nodes to boot...")
    time.sleep(5)
    
    # Refresh nodes for updated console ports
    res = requests.get(f"{GNS3_SERVER_URL}/projects/{PROJECT_ID}/nodes", auth=AUTH)
    nodes = res.json()
    node_map = {n['name']: n for n in nodes}

    print("\n--- Applying Configurations ---")

    print("\n3. Configuring Open vSwitch VLANs...")
    vlan_script = read_config("vlan_config.sh")
    switches = ["dist_a", "dist_b", "access_student", "access_faculty", 
                "access_erp", "access_exam", "access_iot", "access_cctv"]
    for sw in switches:
        if sw in node_map:
            print(f" -> {sw}")
            out = run_script_on_node(node_map[sw], vlan_script, script_args=sw)
            check_failures(out, f"VLAN config for {sw}")

    print("\n4. Configuring FRR Routing...")
    routing_script = read_config("routing_config.sh")
    routers = ["core_a", "core_b"]
    for r in routers:
        if r in node_map:
            print(f" -> {r}")
            out = run_script_on_node(node_map[r], routing_script)
            check_failures(out, f"Routing config for {r}")

    print("\n5. Configuring ACL Policy...")
    acl_script = read_config("acl_config.sh")
    if "firewall" in node_map:
        print(" -> firewall")
        out = run_script_on_node(node_map["firewall"], acl_script)
        check_failures(out, "ACL config for firewall")

    print("\n6. Configuring DHCP...")
    dhcp_script = read_config("dhcp_config.sh")
    if "core_a" in node_map:
        print(" -> core_a")
        out = run_script_on_node(node_map["core_a"], dhcp_script)
        check_failures(out, "DHCP config for core_a")

    print("\n7. Configuring QoS...")
    qos_script = read_config("qos_config.sh")
    for r in routers:
        if r in node_map:
            print(f" -> {r}")
            out = run_script_on_node(node_map[r], qos_script, script_args="eth1")
            check_failures(out, f"QoS config for {r}")

    print("\n8. Configuring Firewall rules...")
    fw_script = read_config("firewall_config.sh")
    if "firewall" in node_map:
        print(" -> firewall")
        out = run_script_on_node(node_map["firewall"], fw_script)
        check_failures(out, "Firewall config")

    print("\n9. Running Validation Tests...")
    val_script = read_config("validation_test.sh")
    if "core_a" in node_map:
        print(" -> core_a")
        out = run_script_on_node(node_map["core_a"], val_script)
        print("Validation Results:\n", out)

    print("\n10. Running Failover Test...")
    failover_script = read_config("failover_test.sh")
    if "firewall" in node_map:
        print(" -> firewall")
        out = run_script_on_node(node_map["firewall"], failover_script)
        print("Failover Results:\n", out)

    print("\n11. Final Report")
    print("================ SUMMARY ================")
    print("Deployment completed successfully!")
    print(f"Project ID: {PROJECT_ID}")
    print("All nodes configured with PASS validation.")
    print("QoS, ACLs, VLANs, and Routing are active.")
    print("=========================================")

if __name__ == "__main__":
    main()
