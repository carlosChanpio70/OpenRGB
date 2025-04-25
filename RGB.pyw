from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
from addons.effects import *
from addons.color import Color
from addons.devices import Devices

brightness_final = 50
color_2_percentage = 0.2
gradient_min_steps = 4
gradient_max_steps = 6
updates_per_second = 30
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]
    
layer_names = Devices().get_layer_names()
purple = Color()
purple.set_HSV(255, 255, brightness_final)
white = Color()
white.set_HSV(0, 0, brightness_final)
colors = [purple, white]

def startup() -> Devices:
    """
    Starts the OpenRGB Client
    :return: The client
    """
    while True:
        try:
            client = OpenRGBClient(name="RGB")
            client.clear()

            devices = Devices()
            for device in client.devices:
                if any(zone.name == "JRAINBOW2" for zone in device.zones):
                    color1 = colors[0].getColor(hue_correction=5)
                else:
                    color1 = colors[0].getColor()
                color2 = colors[1].getColor()

                devices.addDevice(device, color1, color2, color_2_percentage)
            return devices
        except:
            time.sleep(.1)

def update_effects(device, devices) -> None:
    devices.setGradient(device, gradient_min_steps, gradient_max_steps)

    if device.name == names[1]:
        devices.setColorFinal(device, 0, 0)
    if device.name == names[0]:
        devices.setVolume(device)


def apply_layers(device, devices) -> None:
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

        device.set_colors(colors, True)

def main():
    devices=startup()

    start = time.time()
    delay = 0
    desired_delay = 1/(updates_per_second)

    try:
        while True:
                if delay > desired_delay:

                    start = time.time()
                    for device in devices.getDevices():
                        update_effects(device, devices)
                        apply_layers(device, devices)

                time.sleep(1/240)
                delay = time.time() - start
    except:
        main()

if __name__ == "__main__":
    update_volume()
    main()