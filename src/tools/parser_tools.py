from typing import Dict, List, Any

def parse_cdp_output(output: str) -> Dict[str, Any]:
    neighbors = []
    lines = output.split('\n')
    current = {}
    
    for line in lines:
        if 'Device ID:' in line:
            if current:
                neighbors.append(current)
            current = {}
            current['device_id'] = line.split('Device ID:')[1].strip()
        elif 'IP address:' in line:
            current['ip_address'] = line.split('IP address:')[1].strip()
        elif 'Platform:' in line:
            current['platform'] = line.split('Platform:')[1].strip()
        elif 'Interface:' in line:
            current['local_interface'] = line.split('Interface:')[1].strip()
        elif 'Port ID (outgoing port):' in line:
            current['remote_interface'] = line.split('Port ID (outgoing port):')[1].strip()
    
    if current:
        neighbors.append(current)
    
    return neighbors

def parse_interface_ip(output: str) -> List[Dict[str, Any]]:
    interfaces = []
    lines = output.strip().split('\n')
    
    for line in lines[1:]:  # Bỏ header
        parts = line.split()
        if len(parts) >= 2:
            interfaces.append({
                "interface": parts[0],
                "ip_address": parts[1] if parts[1] != "unassigned" else None,
                "status": parts[4] if len(parts) > 4 else "unknown"
            })
    
    return interfaces
