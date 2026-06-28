import time
import logging
import threading
import requests
import urllib3
from functools import wraps

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_proxmox_instance = None
_lock = threading.Lock()

class ProxmoxAPI:
    """Cliente simple para Proxmox API usando requests."""
    def __init__(self, host, token_name, token_value, port=8006, verify_ssl=False, timeout=30):
        self.base_url = f"https://{host}:{port}/api2/json"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"PVEAPIToken={token_name}={token_value}"
        })
        self.session.verify = verify_ssl
        self.timeout = timeout

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json().get('data')

    def get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def post(self, path, **kwargs):
        return self._request('POST', path, **kwargs)

    # Propiedades para acceder a nodos, qemu, lxc
    @property
    def nodes(self):
        return NodeProxy(self)

class NodeProxy:
    def __init__(self, api):
        self.api = api

    def get(self):
        return self.api.get("nodes")

    def __call__(self, node):
        return NodeItemProxy(self.api, node)

class NodeItemProxy:
    def __init__(self, api, node):
        self.api = api
        self.node = node

    @property
    def qemu(self):
        return QemuProxy(self.api, self.node)

    @property
    def lxc(self):
        return LxcProxy(self.api, self.node)

class QemuProxy:
    def __init__(self, api, node):
        self.api = api
        self.node = node

    def get(self):
        return self.api.get(f"nodes/{self.node}/qemu")

    def __call__(self, vmid):
        return QemuItemProxy(self.api, self.node, vmid)

class QemuItemProxy:
    def __init__(self, api, node, vmid):
        self.api = api
        self.node = node
        self.vmid = vmid

    @property
    def status(self):
        return QemuStatusProxy(self.api, self.node, self.vmid)

    def config(self):
        return self.api.get(f"nodes/{self.node}/qemu/{self.vmid}/config")

class QemuStatusProxy:
    def __init__(self, api, node, vmid):
        self.api = api
        self.node = node
        self.vmid = vmid

    def current(self):
        return self.api.get(f"nodes/{self.node}/qemu/{self.vmid}/status/current")

    def start(self):
        return self.api.post(f"nodes/{self.node}/qemu/{self.vmid}/status/start")

    def stop(self):
        return self.api.post(f"nodes/{self.node}/qemu/{self.vmid}/status/stop")

    def shutdown(self, timeout=30):
        return self.api.post(f"nodes/{self.node}/qemu/{self.vmid}/status/shutdown", json={"timeout": timeout})

    def reboot(self, timeout=30):
        return self.api.post(f"nodes/{self.node}/qemu/{self.vmid}/status/reboot", json={"timeout": timeout})

    def reset(self):
        return self.api.post(f"nodes/{self.node}/qemu/{self.vmid}/status/reset")

class LxcProxy:
    def __init__(self, api, node):
        self.api = api
        self.node = node

    def get(self):
        return self.api.get(f"nodes/{self.node}/lxc")

    def __call__(self, vmid):
        return LxcItemProxy(self.api, self.node, vmid)

class LxcItemProxy:
    def __init__(self, api, node, vmid):
        self.api = api
        self.node = node
        self.vmid = vmid

    @property
    def status(self):
        return LxcStatusProxy(self.api, self.node, self.vmid)

    def config(self):
        return self.api.get(f"nodes/{self.node}/lxc/{self.vmid}/config")

class LxcStatusProxy:
    def __init__(self, api, node, vmid):
        self.api = api
        self.node = node
        self.vmid = vmid

    def current(self):
        return self.api.get(f"nodes/{self.node}/lxc/{self.vmid}/status/current")

    def start(self):
        return self.api.post(f"nodes/{self.node}/lxc/{self.vmid}/status/start")

    def stop(self):
        return self.api.post(f"nodes/{self.node}/lxc/{self.vmid}/status/stop")

    def shutdown(self, timeout=20):
        return self.api.post(f"nodes/{self.node}/lxc/{self.vmid}/status/shutdown", json={"timeout": timeout})

    def reboot(self, timeout=20):
        return self.api.post(f"nodes/{self.node}/lxc/{self.vmid}/status/reboot", json={"timeout": timeout})


def get_proxmox_api(config):
    """
    Returns a singleton connection to the Proxmox API using token authentication.
    """
    global _proxmox_instance

    if _proxmox_instance is not None:
        return _proxmox_instance

    with _lock:
        if _proxmox_instance is not None:
            return _proxmox_instance

        try:
            logger.info(f"Создаем соединение с Proxmox: {config.host}")

            _proxmox_instance = ProxmoxAPI(
                host=config.host,
                token_name=config.token_name,
                token_value=config.token_value,
                port=config.port,
                verify_ssl=getattr(config, 'verify_ssl', False),
                timeout=30,
            )

            # Probar conexión
            _proxmox_instance.nodes.get()

            logger.info("Соединение с Proxmox установлено")
            return _proxmox_instance

        except Exception as e:
            logger.error(f"Ошибка подключения к Proxmox: {e}")
            _proxmox_instance = None
            raise


def retry_proxmox_call(max_retries=3, delay=1, catch_exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except catch_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        logger.warning(
                            f"Попытка {attempt + 1}/{max_retries} не удалась: {e}. Повтор через {sleep_time}с"
                        )
                        time.sleep(sleep_time)
            logger.error(f"Все {max_retries} попыток не удались: {last_exception}")
            raise last_exception
        return wrapper
    return decorator