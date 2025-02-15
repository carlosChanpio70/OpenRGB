from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
from effects.Base import *

white_percentage = 0.2
gradient_min_steps = 4
gradient_max_steps = 6
updates_per_second = 30
layers_ids = [
    "layer_1_base",  # * ID 0
    "layer_1_target",  # * ID 1
    "layer_1_timing",  # * ID 2
    "layer_1_current",  # * ID 3
    "layer_1_final",  # * ID 4
    "layer_2_volume",  # * ID 5
]
devices_layers: dict = {}
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]

purple = RGBColor(100, 0, 255)
white = RGBColor(255, 255, 255)
color1 = purple
color2 = white


def startup() -> OpenRGBClient:
    """
    Starts the OpenRGB Client
    :return: The client and devices
    """

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
        for j in layers_ids:
            devices_layers[device.id][j] = []
            for led in device.leds:
                devices_layers[device.id][j].append(None)
    return client


def update_effects(device) -> None:
    layer_1_base = devices_layers[device.id][layers_ids[0]]
    layer_1_target = devices_layers[device.id][layers_ids[1]]
    layer_1_timing = devices_layers[device.id][layers_ids[2]]
    layer_1_current = devices_layers[device.id][layers_ids[3]]
    layer_1_final = devices_layers[device.id][layers_ids[4]]

    if layer_1_base[0] is None:
        layer_1_base = set_base_color(device, color1)

    if layer_1_target[0] is None:
        layer_1_target = set_random_colors(device, color1, color2, white_percentage)

    x = set_timings(device, [layer_1_base, layer_1_target, layer_1_timing, layer_1_current,
                    layer_1_final], gradient_min_steps, gradient_max_steps, color1, color2, white_percentage)
    layer_1_base, layer_1_target, layer_1_timing, layer_1_current, layer_1_final = x

    layer_1_final = gradient(device, layer_1_base, layer_1_target,
                             layer_1_timing, layer_1_current)

    if device.name == names[1]:
        layer_1_final[0] = color1
        
    if device.name == names[0]:
        devices_layers[device.id][layers_ids[5]] = set_volume(device, color1, color2)

    devices_layers[device.id][layers_ids[0]] = layer_1_base
    devices_layers[device.id][layers_ids[1]] = layer_1_target
    devices_layers[device.id][layers_ids[2]] = layer_1_timing
    devices_layers[device.id][layers_ids[3]] = layer_1_current
    devices_layers[device.id][layers_ids[4]] = layer_1_final


def apply_layers(device) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices_layers[device.id][layers_ids[4]][0] is not None:
        colors = devices_layers[device.id][layers_ids[4]]

        if device.name == names[0]:
            for i in range(len(device.colors)):
                if devices_layers[device.id][layers_ids[5]][i] is not None:
                    colors[i] = devices_layers[device.id][layers_ids[5]][i]

        device.set_colors(colors, True)


def main():
    client = startup()

    start = time.time()
    delay = 0
    desired_delay = 1/(updates_per_second)

    global volume
    volume = 0

    while True:
        if delay > desired_delay:
            start = time.time()
            for device in devices:
                update_effects(device)
                apply_layers(device)

        time.sleep(1/240)
        delay = time.time() - start


if __name__ == "__main__":
    update_volume()
    main()