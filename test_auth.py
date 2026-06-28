from proxmoxer import ProxmoxAPI
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("HOST")
token_name = os.getenv("PROXMOX_TOKEN_NAME")
token_value = os.getenv("PROXMOX_TOKEN_VALUE")
port = int(os.getenv("PROXMOX_PORT", 8006))

print(f"Host: {host}")
print(f"Token Name: {token_name}")
print(f"Token Value: {token_value[:5]}...")

# --- Método 1: token_name + token_value (backend explícito) ---
try:
    print("\n🔹 Probando método 1: token_name + token_value (backend='https')")
    proxmox = ProxmoxAPI(
        host=host,
        token_name=token_name,
        token_value=token_value,
        verify_ssl=False,
        port=port,
        timeout=30,
        backend='https'
    )
    nodes = proxmox.nodes.get()
    print("✅ Conexión exitosa!")
    print(f"Nodos: {nodes}")
except Exception as e:
    print(f"❌ Error método 1: {e}")

# --- Método 2: user + password (token completo como user) ---
try:
    print("\n🔹 Probando método 2: user + password (token completo como user)")
    proxmox = ProxmoxAPI(
        host=host,
        user=token_name,          # <- Nombre completo del token
        password=token_value,     # <- Valor secreto
        verify_ssl=False,
        port=port,
        timeout=30,
        backend='https'
    )
    nodes = proxmox.nodes.get()
    print("✅ Conexión exitosa!")
    print(f"Nodos: {nodes}")
except Exception as e:
    print(f"❌ Error método 2: {e}")

# --- Método 3: solo token_name + token_value (sin backend) ---
try:
    print("\n🔹 Probando método 3: token_name + token_value (sin backend)")
    proxmox = ProxmoxAPI(
        host=host,
        token_name=token_name,
        token_value=token_value,
        verify_ssl=False,
        port=port,
        timeout=30,
    )
    nodes = proxmox.nodes.get()
    print("✅ Conexión exitosa!")
    print(f"Nodos: {nodes}")
except Exception as e:
    print(f"❌ Error método 3: {e}")

# --- Método 4: con usuario y contraseña tradicional (para descartar) ---
# (Si tienes credenciales de root, puedes probar)