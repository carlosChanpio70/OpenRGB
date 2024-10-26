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

gradient_min_steps = 5
gradient_max_steps = 10
changes_per_second = 2
layers = [
    "layer_1_base",  # * ID 0
    "layer_1_target",  # * ID 1
    "layer_1",  # * ID 2
    "layer_2",  # * ID 3
    "layer_1_timing",  # * ID 4
    "layer_1_counter"  # * ID 5
]
devices_layers: dict = {}


def timer(func):

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        if end_time - start_time != 0:
            print(f"{func.__name__} took {end_time -
                                          start_time} seconds to execute.")
        return result
    return wrapper


def thread_wrapper(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper


@thread_wrapper
def log_cpu_usage_thread():
    """Thread function to log CPU usage."""
    while True:
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_percent}%")
        time.sleep(1)  # Sleep for 1 second between logs

# Starts the OpenRGB Client and returns the client and devices


def startup() -> OpenRGBClient:
    """
    Starts the OpenRGB Client
    :return: The client and devices
    """

    client = OpenRGBClient(name="RGB")

    ramleft = client.get_devices_by_name("Corsair Vengeance Pro RGB")[0]
    ramright = client.get_devices_by_name("Corsair Vengeance Pro RGB")[1]
    motherboard = client.get_devices_by_name(
        "MSI MPG B550 GAMING PLUS (MS-7C56)")[0]
    global devices
    devices = [ramleft, ramright, motherboard]
    for i in devices:
        i.set_mode(i.modes[0])
        devices_layers[i.id] = {}
        for j in layers:
            devices_layers[i.id][j] = []
            for led in i.leds:
                devices_layers[i.id][j].append(None)
    return client


@thread_wrapper
def update_volume() -> None:
    """"
    Updates the volume global variable
    """

    comtypes.CoInitialize()
    timer_1 = 0

    def set_volume() -> None:
        speaker = interface.QueryInterface(IAudioMeterInformation)
        global volume
        volume = speaker.GetPeakValue()
        if volume > 1 or volume < 0:
            volume = 0

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioMeterInformation._iid_, CLSCTX_ALL, None)

    while True:
        set_volume()
        time.sleep(1/240)

def set_layer_1(input) -> None:
    """
    Defines the colors for layer 1
    :param input: The device to set the colors for
    :param percentage_counter: The current percentage of the animation for switching colors
    """

    def get_color(zone) -> RGBColor:
        """
        Creates a list of random colors based on the zone size

        :param zone: The zone
        """
        
        white = RGBColor(255, 255, 255)
            
        if input.name == "Corsair Vengeance Pro RGB":
            purple = RGBColor(50, 0, 255)
        else:
            purple = RGBColor(100, 0, 255)

        if zone.name == "JRGB1":
            return purple
        else:
            if random.random() < 0.2:
                return white
            else:
                return purple

    def set_color(layer: str) -> None:
        """
        Adds random colors to the layer
        :param layer: The layer to set the colors for
        """

        colors = []
        for i in input.zones:
            for _ in i.leds:
                colors.append(get_color(i))
        devices_layers[input.id][layer] = colors

    def gradient_random_timing(size: int):
        """
        Creates a list of random integers based on the zone size

        :param size: The size of the zone
        :param zone: The zone
        """

        if size == 1:
            return random.randint(gradient_min_steps, gradient_max_steps)
        timings = []
        for _ in range(size):
            timings.append(random.randint(
                gradient_min_steps, gradient_max_steps))
        return timings

    def set_layer_1_gradient() -> None:
        """
        Defines the colors for layer 1 based on the value of volume
        """

        gradient_timing = np.array(devices_layers[input.id][layers[4]])
        gradient_counter = np.array(devices_layers[input.id][layers[5]])
        percent = gradient_counter / gradient_timing

        # Extract red, green, blue values from old_colors and new_colors
        base_colors_rgb = np.array([(color.red, color.green, color.blue)
                                   for color in devices_layers[input.id][layers[0]]])

        target_colors_rgb = np.array(
            [(color.red, color.green, color.blue) for color in devices_layers[input.id][layers[1]]])

        # Calculate gradients for red, green, and blue channels
        r = base_colors_rgb[:, 0] * \
            (1 - percent) + target_colors_rgb[:, 0] * percent
        g = base_colors_rgb[:, 1] * \
            (1 - percent) + target_colors_rgb[:, 1] * percent
        b = base_colors_rgb[:, 2] * \
            (1 - percent) + target_colors_rgb[:, 2] * percent

        # Combine the calculated red, green, blue values back into RGBColor objects
        output = [RGBColor(int(r[i]), int(g[i]), int(b[i]))
                  for i in range(len(r))]

        devices_layers[input.id][layers[2]] = output

    if devices_layers[input.id][layers[0]][0] == None:
        set_color(layers[0])
        set_color(layers[1])

    if devices_layers[input.id][layers[4]][0] == None:
        devices_layers[input.id][layers[4]
                                 ] = gradient_random_timing(len(input.leds))
        devices_layers[input.id][layers[5]] = [0] * len(input.leds)

    for i in range(len(input.leds)):
        devices_layers[input.id][layers[5]][i] += 1
        if devices_layers[input.id][layers[4]][i] <= devices_layers[input.id][layers[5]][i]:
            devices_layers[input.id][layers[4]][i] = gradient_random_timing(1)
            devices_layers[input.id][layers[5]][i] = 0
            # Switch base and target colors and get new target colors
            devices_layers[input.id][layers[0]][i] = devices_layers[input.id][layers[1]][i]
            for j in devices:
                for k in j.zones:
                    for l in k.leds:
                        if l.id == input.leds[i].id:
                            zone = k
            devices_layers[input.id][layers[1]][i] = get_color(zone)

    set_layer_1_gradient()

def set_layer_2(input) -> None:
    """
    Defines the colors for layer 2 based on the value of volume
    :param input: The device to set the colors for
    """

    def gradient(percent) -> RGBColor:
        color1 = [50, 0, 255]
        color2 = [255, 255, 255]
        return RGBColor(int(color1[0] * (1 - percent) + color2[0] * percent), int(color1[1] * (1 - percent) + color2[1] * percent), int(color1[2] * (1 - percent) + color2[2] * percent))

    if input.name == "Corsair Vengeance Pro RGB":
        colors = []
        for i in range(len(input.leds)):
            colors.append(None)

        for i in input.zones:
            led_id = i.leds[0].id+1
            size = len(i.leds)-2
            for i in range(size):
                displayed_volume = size*volume
                if i < int(displayed_volume):
                    colors[led_id + i] = RGBColor(255, 255, 255)
                else:
                    colors[led_id + i] = gradient(displayed_volume-i)
                    break

        devices_layers[input.id][layers[3]] = colors

def apply_layers(input) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices_layers[input.id][layers[2]][0] is not None:
        colors = devices_layers[input.id][layers[2]]

        if input.name == "Corsair Vengeance Pro RGB":
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
    desired_delay = 1/(changes_per_second*((gradient_min_steps+gradient_max_steps)/2))

    global volume, volume1
    volume = 0
    volume1 = 0

    update_volume()

    # log_cpu_usage_thread()


    try:
        while True:
            if delay > desired_delay:
                start = time.time()

                for i in devices:
                    set_layer_1(i)
                    set_layer_2(i)

            for i in devices:
                if volume1 != volume and delay < desired_delay:
                    set_layer_2(i)
                apply_layers(i)

            volume1 = volume
            time.sleep(1/480)
            delay = time.time() - start

    except ConnectionAbortedError:
        client.disconnect()
        main()


if __name__ == "__main__":
    main()