from ppadb.client import Client as AdbClient

def trigger_camera_shutter():
    try:
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()
        if not devices:
            print("ADB: No device found.")
            return False
        
        device = devices[0]
        # Keycode 25 is Volume Down, often acts as Shutter
        device.input_keyevent(25) 
        return True
    except Exception as e:
        print(f"ADB Error: {e}")
        return False