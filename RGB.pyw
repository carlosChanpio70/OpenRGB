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
            devices.addDevice(client.get_devices_by_name(names[0])[0])
            devices.addDevice(client.get_devices_by_name(names[0])[1])
            devices.addDevice(client.get_devices_by_name(names[1])[0])

            return devices
        except:
            time.sleep(.1)


def brightness_adjust(color: RGBColor, brightness) -> RGBColor:
    """
    Adjusts the brightness of a color
    :param color: The color to adjust
    :return: The adjusted color
    """
    return RGBColor(int(color.red * brightness),
                    int(color.green * brightness),
                    int(color.blue * brightness))


def update_effects(device, devices) -> None:
    if any(zone.name == "JRAINBOW2" for zone in device.zones):
        color1 = colors[0].get_color(hue_correction=5)
        color2 = colors[1].get_color()
    else:
        color1 = colors[0].get_color()
        color2 = colors[1].get_color()

    if devices.getLayer(device, layer_names[0])[0] is None:
        devices.setLayer(device, layer_names[0],
                         set_base_color(device, color1))

    if devices.getLayer(device, layer_names[1])[0] is None:
        devices.setLayer(device, layer_names[1],
                         set_random_colors(device, color1, color2, color_2_percentage))

    devices.setLayer(device, tuple(layer_names[:5]),
                     set_timings(device,
                                 [devices.getLayer(device, ln)
                                  for ln in layer_names[:5]],
                                 gradient_min_steps, gradient_max_steps, color1, color2, color_2_percentage))

    devices.setLayer(device, layer_names[4],
                     gradient(device, [devices.getLayer(device, ln) for ln in layer_names[:4]]))

    if device.name == names[1]:
        layer = devices.getLayer(device, layer_names[4])
        layer[0] = color1
        devices.setLayer(device, layer_names[4], layer)
    if device.name == names[0]:
        devices.setLayer(device, layer_names[5],
                         set_volume(device, color1, color2))


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

    while True:
        try:
            if delay > desired_delay:

                start = time.time()
                for device in devices.getDevices():
                    update_effects(device, devices)
                    apply_layers(device, devices)

            time.sleep(1/240)
            delay = time.time() - start
        except ConnectionAbortedError:
            startup()


if __name__ == "__main__":
    update_volume()
    main()