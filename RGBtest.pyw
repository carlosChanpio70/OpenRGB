import random
import psutil
import comtypes
import threading
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from .effects.Base import *

gradient_min_steps = 4
gradient_max_steps = 6
updates_per_second = 30
layers = [
    "layer_1_base",  # * ID 0
    "layer_1_target",  # * ID 1
    "layer_1",  # * ID 2
    "layer_2",  # * ID 3
    "layer_1_timing",  # * ID 4
    "layer_1_counter"  # * ID 5
]
devices_layers: dict = {}
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]

def startup() -> OpenRGBClient:
    """
    Starts the OpenRGB Client
    :return: The client and devices
    """

    client = OpenRGBClient(name="RGB")
    client.clear()
        
    global devices
    devices=[]
    devices.append(client.get_devices_by_name(names[0])[0])
    devices.append(client.get_devices_by_name(names[0])[1])
    devices.append(client.get_devices_by_name(names[1])[0])
    
    for i in devices:
        i.set_mode(i.modes[0])
        devices_layers[i.id] = {}
        for j in layers:
            devices_layers[i.id][j] = []
            for led in i.leds:
                devices_layers[i.id][j].append(None)
    return client

def update_layer(input, function) -> None:
    
    pass

def apply_layers(input) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices_layers[input.id][layers[2]][0] is not None:
        colors = devices_layers[input.id][layers[2]]

        if input.name == names[0]:
            for i in range(len(input.colors)):
                if devices_layers[input.id][layers[3]][i] is not None:
                    colors[i] = devices_layers[input.id][layers[3]][i]

        input.set_colors(colors, True)


def main():
    try:

        client = startup()
    except:
        time.sleep(5)
        main()

    start = time.time()
    delay = 0
    desired_delay = 1/(updates_per_second)

    global volume, volume1
    volume = 0
    volume1 = 0

    update_volume()

    # log_cpu_usage_thread()


    try:
        while True:
            if delay > desired_delay:
                
                
            for i in devices:
                set_volume(i,names[0])
                apply_layers(i)

            volume1 = volume
            time.sleep(1/480)
            delay = time.time() - start

    except:
        client.disconnect()
        main()


if __name__ == "__main__":
    main()