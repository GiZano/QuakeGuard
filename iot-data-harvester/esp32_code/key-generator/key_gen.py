"""
Script: IoT Identity & Payload Generator
Author: GiZano
Description: 
    Generates valid ECDSA (NIST256p) key pairs and signed test payloads 
    simulating the QuakeFinder IoT firmware.
    Useful for testing Backend APIs without physical hardware.

Dependencies:
    pip install ecdsa
"""

import time
import json
import binascii
from typing import Tuple
from ecdsa import SigningKey, NIST256p

def generate_identity() -> Tuple[SigningKey, str]:
    """
    Generates a new ECDSA Key Pair using the NIST256p curve (secp256r1).
    This matches the cryptography standard used by the ESP32 firmware.

    Returns:
        Tuple[SigningKey, str]: 
            - The Private Key object (for signing).
            - The Public Key string in Hexadecimal format (for the database).
    """
    print("--- 🔐 GENERATING IOT IDENTITY ---")
    
    # 1. Generate Private Key (NIST256p / SECP256R1)
    # The private key is the secret "identity" of the device.
    private_key = SigningKey.generate(curve=NIST256p)
    
    # 2. Derive Public Key
    # The public key is derived mathematically from the private key.
    # It is safe to share and is used by the server to verify signatures.
    public_key = private_key.verifying_key
    
    # Convert to Hex strings for storage/transmission
    priv_hex = binascii.hexlify(private_key.to_string()).decode()
    pub_hex = binascii.hexlify(public_key.to_string()).decode()
    
    print(f"🔑 PRIVATE KEY (Keep Secret): {priv_hex}")
    print(f"🌍 PUBLIC KEY  (Database):    {pub_hex}")
    print("-" * 60)
    
    return private_key, pub_hex

def create_signed_payload(signing_key: SigningKey, sensor_id: int = 101) -> dict:
    """
    Creates a simulated sensor payload and signs it digitally.

    Args:
        signing_key (SigningKey): The private key used to sign the data.
        sensor_id (int): The ID of the simulated sensor.

    Returns:
        dict: The complete JSON payload ready for the HTTP POST request.
    """
    print("\n--- 📝 CREATING SIGNED PAYLOAD ---")
    
    # Simulated Sensor Data
    seismic_value = 250         # Integer representation (e.g., Ratio 2.50 * 100)
    timestamp = int(time.time()) # Current Unix Timestamp
    
    # Message Construction
    # CRITICAL: This format MUST match the firmware logic exactly: "value:timestamp"
    message_to_sign = f"{seismic_value}:{timestamp}"
    print(f"ℹ️  Raw Data String: '{message_to_sign}'")
    
    # Digital Signature Generation
    # We sign the UTF-8 bytes of the string using the Private Key
    signature = signing_key.sign(message_to_sign.encode('utf-8'))
    signature_hex = binascii.hexlify(signature).decode()
    
    print(f"✍️  ECDSA Signature: {signature_hex}")
    
    # JSON Construction
    payload = {
        "value": seismic_value,
        "misurator_id": sensor_id,
        "device_timestamp": timestamp,
        "signature_hex": signature_hex
    }
    
    return payload

if __name__ == "__main__":
    try:
        # 1. Generate credentials
        my_private_key, my_public_key_hex = generate_identity()
        
        # 2. Create a test packet
        packet = create_signed_payload(my_private_key, sensor_id=101)
        
        # 3. Output results
        print("\n--- 🚀 READY FOR POSTMAN / CURL ---")
        print(json.dumps(packet, indent=4))
        
        print("\n[INSTRUCTIONS]")
        print(f"1. Insert the PUBLIC KEY above into your database for sensor ID {packet['misurator_id']}.")
        print("2. Send the JSON payload to: POST /misurations/")
        
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")