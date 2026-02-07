import os

Import("env")

# Percorso del file di configurazione
config_path = "esp32_config.env"

print(f"🔍 Looking for configuration in: {config_path}")

if os.path.isfile(config_path):
    print("✅ Config file found! Injecting environment variables...")
    try:
        with open(config_path) as f:
            for line in f:
                # Ignora commenti e righe vuote
                if line.strip().startswith("#") or not line.strip():
                    continue
                
                # Split key=value
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    
                    # Pulisci eventuali virgolette extra dal file .env se presenti
                    # (PlatformIO le gestisce meglio se gliele passiamo pulite e le aggiungiamo noi dopo)
                    value = value.strip().strip('"').strip("'")
                    
                    # Se è un numero (come SERVER_PORT o SENSOR_ID), lo passiamo come numero
                    # Se è una stringa (come WIFI_SSID), dobbiamo aggiungere le virgolette escape per C++
                    if value.isdigit():
                        env_value = value
                    else:
                        # TRICK: Escape delle virgolette per C++: "MyWiFi" diventa \"MyWiFi\"
                        env_value = f'\\"{value}\\"'
                    
                    print(f"   ➡️  Setting {key} = {value}")
                    env.Append(CPPDEFINES=[(key, env_value)])
                    
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
else:
    print(f"⚠️  WARNING: {config_path} not found! Using default/fallback values if defined in code.")