from system.sensors import get_status, get_battery_status, get_temperatures

print("=== Probando sensors.py ===\n")

# 1. Temperaturas
print("1. Temperaturas:")
temps = get_temperatures()
if temps:
    for t in temps:
        print(f"   {t['sensor']}: {t['temp']:.1f}°C")
else:
    print("   No se detectaron sensores de temperatura")

# 2. Batería
print("\n2. Estado de batería:")
battery = get_battery_status()
if battery["has_battery"]:
    print(f"   Porcentaje: {battery['percent']}%")
    print(f"   Estado: {battery['status']}")
    print(f"   ¿Cargando? {battery['is_charging']}")
else:
    print("   No se detectó batería")

# 3. Status completo
print("\n3. Status completo:")
print(get_status())