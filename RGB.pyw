from openrgb import OpenRGBClient
import time
from addons.color import Color
from addons.devices import Devices
import addons.volume as volume
from comtypes import CLSCTX_ALL
from addons.effects import timer

class NoDevicesFoundError(RuntimeError):
    """Raised when the OpenRGBClient reports no hardware devices."""
    pass

brightness_final = 50
color_2_percentage = 0.2
gradient_min_steps = 4
gradient_max_steps = 6
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]
    
layer_names = Devices().get_layer_names()
purple = Color()
purple.set_HSV(255, 255, brightness_final)
white = Color()
white.set_HSV(0, 0, brightness_final)
colors = [purple, white]

def startup():
    """
    Starts the OpenRGB Client
    :return: The client
    """
    while True:
        try:
            client = OpenRGBClient()
            
            
            devices = Devices()
            if not client.devices:                          # empty list is falsy
                # no hardware detected yet; raise a specific exception so
                # the outer loop can retry without swallowing unrelated
                # errors
                raise NoDevicesFoundError("no devices found")
            else:
                for device in client.devices:
                    device.set_mode(0)
                    if any(zone.name == "JRAINBOW2" for zone in device.zones):
                        color1 = colors[0].getColor(hue_correction=5)
                    else:
                        color1 = colors[0].getColor()
                    color2 = colors[1].getColor()

                    devices.addDevice(device, color1, color2, color_2_percentage)
                return client,devices
        except:
            time.sleep(.1)

def update_effects(device, devices) -> None:
    devices.setGradient(device, gradient_min_steps, gradient_max_steps)

    if device.name == names[1]:
        devices.setColorFinal(device, 0, 0)
    if device.name == names[0]:
        devices.setVolume(device,volume)

def color_set(device, devices) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices.getLayer(device, layer_names[4])[0] is not None:
        colors = devices.getLayer(device, layer_names[4])

        if device.name == names[0]:
            for i in range(len(device.colors)):
                if devices.getLayer(device, layer_names[5])[i] is not None:
                    colors[i] = devices.getLayer(device, layer_names[5])[i]

        device.colors = colors

def main():
    client,devices=startup()

    fps = 24
    frame_time = 1/fps
    
    try:
        while True:
            start = time.time()

            for device in devices.getDevices():
                update_effects(device, devices)
                color_set(device, devices)
            client.show()

            elapsed = time.time() - start
            sleep_time = frame_time - elapsed
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except Exception as e:
        print(e)
        main()

if __name__ == "__main__":
    volume.start_volume_monitor()
    main()