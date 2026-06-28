import asyncio
from proxmox.client import get_proxmox_api
from config import PROXMOX

async def test_connection():
    try:
        proxmox = get_proxmox_api(PROXMOX)
        nodes = proxmox.nodes.get()
        print("✅ Conexión exitosa a Proxmox!")
        print(f"Nodos: {nodes}")
        
        # Probar listar VMs
        vms = proxmox.nodes("pve").qemu.get()
        print(f"VMs encontradas: {len(vms)}")
        for vm in vms:
            print(f"  - {vm.get('name', 'sin nombre')} (ID: {vm['vmid']})")
            
        # Probar listar LXC
        lxcs = proxmox.nodes("pve").lxc.get()
        print(f"LXCs encontrados: {len(lxcs)}")
        for ct in lxcs:
            print(f"  - {ct.get('name', 'sin nombre')} (ID: {ct['vmid']})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())