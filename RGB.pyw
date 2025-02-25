from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
from effects.Base import *

color_2_percentage = 0.2
gradient_min_steps = 8
gradient_max_steps = 10
updates_per_second = 30
devices_layers: dict = {}
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]
layer_names = [
    "layer_1_base",  # * ID 0
    "layer_1_target",  # * ID 1
    "layer_1_timing",  # * ID 2
    "layer_1_current",  # * ID 3
    "layer_1_final",  # * ID 4
    "layer_2_volume",  # * ID 5
]

purple = RGBColor(100, 0, 255)
white = RGBColor(255, 255, 255)
color1 = purple
color2 = white


def startup() -> OpenRGBClient:
    """
    Starts the OpenRGB Client
    :return: The client
    :global: devices
    """

    while True:
        try:
            client = OpenRGBClient(name="RGB")
            client.clear()

            global devices
            devices = []
            devices.append(client.get_devices_by_name(names[0])[0])
            devices.append(client.get_devices_by_name(names[0])[1])
            devices.append(client.get_devices_by_name(names[1])[0])

            for device in devices:
                device.set_mode(device.modes[0])
                devices_layers[device.id] = {}
                for j in layer_names:
                    devices_layers[device.id][j] = []
                    for led in device.leds:
                        devices_layers[device.id][j].append(None)
            return client
        except:
            time.sleep(.1)


def update_effects(device) -> None:
    if devices_layers[device.id][layer_names[0]][0] is None:
        devices_layers[device.id][layer_names[0]
                                  ] = set_base_color(device, color1)

    if devices_layers[device.id][layer_names[1]][0] is None:
        devices_layers[device.id][layer_names[1]] = set_random_colors(
            device, color1, color2, color_2_percentage)

    devices_layers[device.id][tuple(layer_names[:5])] = set_timings(device,
                                                                    [devices_layers[device.id][ln]
                                                                        for ln in layer_names[:5]],
                                                                    gradient_min_steps, gradient_max_steps, color1, color2, color_2_percentage)

    devices_layers[device.id][layer_names[4]] = gradient(
        device, [devices_layers[device.id][ln] for ln in layer_names[:4]])

    if device.name == names[1]:
        devices_layers[device.id][layer_names[4]][0] = color1
    if device.name == names[0]:
        devices_layers[device.id][layer_names[5]
                                  ] = set_volume(device, color1, color2)


def apply_layers(device) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices_layers[device.id][layer_names[4]][0] is not None:
        colors = devices_layers[device.id][layer_names[4]]

        if device.name == names[0]:
            for i in range(len(device.colors)):
                if devices_layers[device.id][layer_names[5]][i] is not None:
                    colors[i] = devices_layers[device.id][layer_names[5]][i]

        device.set_colors(colors, True)


def main():
    startup()

    start = time.time()
    delay = 0
    desired_delay = 1/(updates_per_second)

    while True:
        try:
            if delay > desired_delay:

                start = time.time()
                for device in devices:
                    update_effects(device)
                    apply_layers(device)

            time.sleep(1/240)
            delay = time.time() - start
        except ConnectionAbortedError:
            startup()


if __name__ == "__main__":
    update_volume()
    main()
