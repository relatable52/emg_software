from ppadb.client import Client as AdbClient
import time

def getDevice():
    # Default is "127.0.0.1" and 5037
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    if (len(devices) < 0):
        print("0 device")
        return 0

    return devices[0]

device = getDevice()

def openCameraApp(device):
   device.input_keyevent(25)  # KEYCODE_CAMERA
   time.sleep(3)
   device.input_keyevent(25)   # KEYCODE_BACK
    
openCameraApp(device)
