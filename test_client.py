from dotenv import load_dotenv
from proxmox.client import get_proxmox_api
from config import PROXMOX

load_dotenv()

try:
    proxmox = get_proxmox_api(PROXMOX)
    nodes = proxmox.nodes.get()
    print("✅ Conexión exitosa!")
    print(f"Nodos: {nodes}")
    
    # Probar VMs
    vms = proxmox.nodes("pve").qemu.get()
    print(f"VMs: {vms}")
    
    # Probar LXC
    lxcs = proxmox.nodes("pve").lxc.get()
    print(f"LXCs: {lxcs}")
    
except Exception as e:
    print(f"❌ Error: {e}")