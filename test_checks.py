from system.checks import check_cpu_temp, check_cpu_usage, check_ram_usage

print("=== Probando checks.py ===\n")

# CPU Temperature
alert, value = check_cpu_temp()
print(f"1. CPU Temperature: {value}°C")
print(f"   ¿Alerta? {alert}")

# CPU Usage
alert, value = check_cpu_usage()
print(f"2. CPU Usage: {value}%")
print(f"   ¿Alerta? {alert}")

# RAM Usage
alert, value = check_ram_usage()
print(f"3. RAM Usage: {value}%")
print(f"   ¿Alerta? {alert}")