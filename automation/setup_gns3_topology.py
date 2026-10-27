import requests
import json
import time
import sys

# --- CONFIGURATION ---
GNS3_SERVER_URL = "http://localhost:3080/v2"
# Replace with your GNS3 credentials if authentication is enabled
AUTH = ('admin', 'O5lJGEKu2QavRFTXnVPwajTxurl55aiSUiGzbTMwF55wizNpNqIFji8SpBbYZftr') 
PROJECT_NAME = "Smart_Campus_Network"

# Note: You must have these templates installed in your GNS3.
# Update these names to exactly match your GNS3 templates.
ROUTER_TEMPLATE_NAME = "FRR Router"
SWITCH_TEMPLATE_NAME = "Ethernet switch"
PC_TEMPLATE_NAME = "VPCS"

def create_project(name):
    print(f"Creating project '{name}'...")
    url = f"{GNS3_SERVER_URL}/projects"
    data = {"name": name}
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code == 201:
        return response.json()['project_id']
    elif response.status_code == 409: # Project exists
        print("Project already exists, finding ID...")
        res = requests.get(url, auth=AUTH).json()
        for p in res:
            if p['name'] == name:
                return p['project_id']
    else:
        print(f"Error creating project: {response.text}")
        sys.exit(1)

def get_template_id(name):
    url = f"{GNS3_SERVER_URL}/templates"
    response = requests.get(url, auth=AUTH)
    for template in response.json():
        if template['name'] == name:
            template_id = template['template_id']
            print(f"Verified template '{name}' (ID: {template_id})")
            return template_id
    print(f"ERROR: Template '{name}' not found. Please check your GNS3 templates.")
    sys.exit(1)

def get_computes():
    url = f"{GNS3_SERVER_URL}/computes"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        computes = response.json()
        print("Available Computes:")
        for c in computes:
            print(f"  Name: {c.get('name')}, ID: {c.get('compute_id')}, Host: {c.get('host')}")
        return computes
    else:
        print(f"Error fetching computes: {response.text}")
        sys.exit(1)

def get_compute_ids(computes):
    local_compute_id = None
    vm_compute_id = None

    for c in computes:
        if c.get("compute_id") == "local":
            local_compute_id = "local"
        if c.get("name") == "GNS3 VM (GNS3 VM)":
            vm_compute_id = c.get("compute_id")

    if not local_compute_id:
        print("ERROR: local compute was not found")
        sys.exit(1)

    if not vm_compute_id:
        print("ERROR: GNS3 VM compute was not found")
        sys.exit(1)

    return local_compute_id, vm_compute_id

def get_existing_nodes(project_id):
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        nodes = response.json()
        node_map = {}
        for n in nodes:
            node_map[n['name']] = n['node_id']
        return node_map
    else:
        print(f"Error fetching existing nodes: {response.text}")
        sys.exit(1)

def get_existing_links(project_id):
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/links"
    response = requests.get(url, auth=AUTH)
    if response.status_code == 200:
        links = response.json()
        link_set = set()
        for l in links:
            nodes = l.get('nodes', [])
            if len(nodes) == 2:
                n1 = nodes[0]
                n2 = nodes[1]
                ep1 = (n1['node_id'], n1['adapter_number'], n1['port_number'])
                ep2 = (n2['node_id'], n2['adapter_number'], n2['port_number'])
                link_set.add(tuple(sorted((ep1, ep2))))
        return link_set
    else:
        print(f"Error fetching existing links: {response.text}")
        sys.exit(1)

def create_node(project_id, template_id, compute_id, name, x, y, existing_nodes):
    if name in existing_nodes:
        print(f"Node '{name}' already exists. Reusing ID: {existing_nodes[name]}")
        return existing_nodes[name]
        
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/templates/{template_id}"
    data = {
        "x": x,
        "y": y,
        "compute_id": compute_id
    }
    
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code == 201:
        node = response.json()
        node_id = node['node_id']
        
        # Rename the node to the desired name
        put_url = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes/{node_id}"
        put_data = {"name": name}
        put_res = requests.put(put_url, json=put_data, auth=AUTH)
        if put_res.status_code != 200:
            print(f"Warning: Node created but renaming to '{name}' failed.")
            print(f"  HTTP Status: {put_res.status_code}")
            print(f"  URL: {put_url}")
            print(f"  Response: {put_res.text}")
            
        print(f"Created new node '{name}' (ID: {node_id})")
        return node_id
    else:
        print(f"Error creating node '{name}' from template {template_id}")
        print(f"  HTTP Status: {response.status_code}")
        print(f"  URL: {url}")
        print(f"  Request JSON: {json.dumps(data)}")
        print(f"  Response: {response.text}")
        sys.exit(1)

def create_link(project_id, node1_id, adapter1, port1, node2_id, adapter2, port2, existing_links):
    ep1 = (node1_id, adapter1, port1)
    ep2 = (node2_id, adapter2, port2)
    link_tuple = tuple(sorted((ep1, ep2)))
    
    if link_tuple in existing_links:
        print(f"Link between {node1_id} and {node2_id} already exists. Skipping.")
        return

    url = f"{GNS3_SERVER_URL}/projects/{project_id}/links"
    data = {
        "nodes": [
            {"node_id": node1_id, "adapter_number": adapter1, "port_number": port1},
            {"node_id": node2_id, "adapter_number": adapter2, "port_number": port2}
        ]
    }
    response = requests.post(url, json=data, auth=AUTH)
    if response.status_code != 201:
        print(f"Error creating link:")
        print(f"  HTTP Status: {response.status_code}")
        print(f"  URL: {url}")
        print(f"  Request JSON: {json.dumps(data)}")
        print(f"  Response: {response.text}")
    else:
        print(f"Created link between {node1_id} and {node2_id}")

def start_all_nodes(project_id):
    print("Starting all nodes...")
    url = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes/start"
    requests.post(url, auth=AUTH)

def cleanup_unexpected_nodes(project_id):
    expected_names = {
        "core_a", "core_b", "dist_a", "dist_b", 
        "access_student", "access_exam", "access_cctv", 
        "border_router", "student_pc", "exam_pc", "cctv_camera"
    }
    
    url_nodes = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes"
    res_nodes = requests.get(url_nodes, auth=AUTH)
    if res_nodes.status_code != 200:
        print("Error fetching nodes for cleanup")
        return
        
    nodes = res_nodes.json()
    unexpected_nodes = []
    expected_count = 0
    for n in nodes:
        if n['name'] in expected_names:
            expected_count += 1
        else:
            unexpected_nodes.append(n)
            
    if not unexpected_nodes:
        print(f"Expected nodes found: {expected_count}")
        print("Duplicate nodes removed: 0")
        print("Existing links preserved.")
        return
        
    url_links = f"{GNS3_SERVER_URL}/projects/{project_id}/links"
    res_links = requests.get(url_links, auth=AUTH)
    links = res_links.json() if res_links.status_code == 200 else []
    
    removed_nodes_count = 0
    for un in unexpected_nodes:
        node_id = un['node_id']
        
        for l in links:
            nodes_in_link = [n['node_id'] for n in l.get('nodes', [])]
            if node_id in nodes_in_link:
                link_id = l['link_id']
                requests.delete(f"{GNS3_SERVER_URL}/projects/{project_id}/links/{link_id}", auth=AUTH)
                
        requests.delete(f"{GNS3_SERVER_URL}/projects/{project_id}/nodes/{node_id}", auth=AUTH)
        removed_nodes_count += 1
        
    print(f"Expected nodes found: {expected_count}")
    print(f"Duplicate nodes removed: {removed_nodes_count}")
    print("Existing links preserved.")

def main():
    try:
        print("Connecting to GNS3 API...")
        res = requests.get(f"{GNS3_SERVER_URL}/version", auth=AUTH)
        if res.status_code != 200:
            print(f"Failed to connect or authenticate. Status Code: {res.status_code}")
            return
        print(f"Connected to GNS3 Server version: {res.json()['version']}")
    except Exception as e:
        print(f"Could not reach GNS3 API. Error: {e}")
        return

    project_id = create_project(PROJECT_NAME)
    print(f"Project ID: {project_id}")

    # Check for existing topology and rename core_a2 if necessary
    url_nodes = f"{GNS3_SERVER_URL}/projects/{project_id}/nodes"
    res = requests.get(url_nodes, auth=AUTH)
    if res.status_code == 200:
        nodes = res.json()
        names = set(n['name'] for n in nodes)
        
        renamed = False
        if "core_a2" in names and "core_a" not in names:
            node_id_to_rename = next(n['node_id'] for n in nodes if n['name'] == "core_a2")
            put_res = requests.put(f"{GNS3_SERVER_URL}/projects/{project_id}/nodes/{node_id_to_rename}", json={"name": "core_a"}, auth=AUTH)
            if put_res.status_code == 200:
                renamed = True
                names.remove("core_a2")
                names.add("core_a")
                
        expected_names = {
            "core_a", "core_b", "dist_a", "dist_b", 
            "access_student", "access_exam", "access_cctv", 
            "border_router", "student_pc", "exam_pc", "cctv_camera"
        }
        
        if expected_names.issubset(names):
            print("Existing Smart_Campus_Network detected.")
            print("Expected topology already exists.")
            if renamed:
                print("Renamed core_a2 -> core_a.")
            print("No nodes recreated.")
            print("No links recreated.")
            print("Cleanup complete.")
            print("\nFinal nodes in project:", list(names))
            if "core_a" in names:
                print("Verification passed: 'core_a' exists.")
            return

    cleanup_unexpected_nodes(project_id)

    computes = get_computes()
    local_compute_id, vm_compute_id = get_compute_ids(computes)

    switch_template = get_template_id(SWITCH_TEMPLATE_NAME)
    router_template = get_template_id(ROUTER_TEMPLATE_NAME)
    pc_template = get_template_id(PC_TEMPLATE_NAME)
    
    existing_nodes = get_existing_nodes(project_id)
    existing_links = get_existing_links(project_id)

    print("Creating nodes (Core, Distribution, Access, PCs)...")
    core_a = create_node(project_id, router_template, vm_compute_id, "core_a", 0, -200, existing_nodes)
    core_b = create_node(project_id, router_template, vm_compute_id, "core_b", 200, -200, existing_nodes)
    
    dist_a = create_node(project_id, switch_template, local_compute_id, "dist_a", -100, 0, existing_nodes)
    dist_b = create_node(project_id, switch_template, local_compute_id, "dist_b", 300, 0, existing_nodes)
    
    access_student = create_node(project_id, switch_template, local_compute_id, "access_student", -200, 200, existing_nodes)
    access_exam = create_node(project_id, switch_template, local_compute_id, "access_exam", 0, 200, existing_nodes)
    access_cctv = create_node(project_id, switch_template, local_compute_id, "access_cctv", 200, 200, existing_nodes)
    
    border_router = create_node(project_id, router_template, vm_compute_id, "border_router", 100, -400, existing_nodes)
    
    student_pc = create_node(project_id, pc_template, local_compute_id, "student_pc", -200, 300, existing_nodes)
    exam_pc = create_node(project_id, pc_template, local_compute_id, "exam_pc", 0, 300, existing_nodes)
    cctv_camera = create_node(project_id, pc_template, local_compute_id, "cctv_camera", 200, 300, existing_nodes)

    print("Wiring the topology...")
    create_link(project_id, border_router, 0, 0, core_a, 0, 0, existing_links)
    create_link(project_id, border_router, 1, 0, core_b, 0, 0, existing_links)
    
    create_link(project_id, core_a, 1, 0, core_b, 1, 0, existing_links)
    
    create_link(project_id, core_a, 2, 0, dist_a, 0, 1, existing_links)
    create_link(project_id, core_a, 3, 0, dist_b, 0, 1, existing_links)
    create_link(project_id, core_b, 2, 0, dist_a, 0, 2, existing_links)
    create_link(project_id, core_b, 3, 0, dist_b, 0, 2, existing_links)
    
    create_link(project_id, dist_a, 0, 3, access_student, 0, 1, existing_links)
    create_link(project_id, dist_a, 0, 4, access_exam, 0, 1, existing_links)
    create_link(project_id, dist_b, 0, 3, access_cctv, 0, 1, existing_links)
    
    create_link(project_id, access_student, 0, 2, student_pc, 0, 0, existing_links)
    create_link(project_id, access_exam, 0, 2, exam_pc, 0, 0, existing_links)
    create_link(project_id, access_cctv, 0, 2, cctv_camera, 0, 0, existing_links)

    print("Topology created successfully!")
    
    # Verification step
    print("\nVerifying final topology nodes...")
    res = requests.get(f"{GNS3_SERVER_URL}/projects/{project_id}/nodes", auth=AUTH)
    if res.status_code == 200:
        final_names = [n['name'] for n in res.json()]
        print("Final nodes in project:", final_names)
        if "core_a" in final_names:
            print("Verification passed: 'core_a' exists.")
        else:
            print("Verification failed: 'core_a' is missing.")
            
    start = input("\nStart all nodes now? (y/n): ")
    if start.lower() == 'y':
        start_all_nodes(project_id)
        print("Nodes are booting up.")
        
if __name__ == "__main__":
    main()
