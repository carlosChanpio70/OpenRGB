import random
import psutil
import comtypes
import threading
from openrgb.utils import RGBColor
import time
import numpy
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

def timer(func):
    """
    Decorator to measure the execution time of a function
    """
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
    """
    Decorator to run a function in a separate thread
    """
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@thread_wrapper
def log_cpu_usage():
    """Function to log CPU usage."""
    while True:
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_percent}%")
        time.sleep(1)  # Sleep for 1 second between logs

@thread_wrapper
def update_volume() -> None:
    """"
    Updates the volume global variable based on the volume of the speakers
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

def set_base_color(device, color:RGBColor) -> list:
    """
    Sets the base color for a layer
    :param input: The device to set the colors for
    :param color: The color to set
    :return: The layer with the base color
    """

    colors = []
    for i in device.zones:
        for _ in i.leds:
            colors.append(color)
    return colors

def set_random_color(color1: RGBColor, color2: RGBColor, probability: float) -> RGBColor:
    """
    Sets random color for a led
    :param color1: The base color to set
    :param color2: The second color to set
    :param probability: The probability of setting a color
    :return: The random color
    """
        
    if random.random() < probability:
        return color2
    else:
        return color1

def set_random_colors(device, color1: RGBColor, color2: RGBColor, probability: float) -> list:
    """
    Sets random colors for a layer
    :param device: The device to set the colors for
    :param color1: The base color to set
    :param color2: The second color to set
    :param probability: The probability of setting a color
    :return: The layer with randomzied colors
    """
    
    layer = []
    
    for i in device.zones:
        for _ in i.leds:
            layer.append(set_random_color(color1, color2, probability))

    return layer

def set_timings(device,layers:list,timing_low:int,timing_high:int,color1:RGBColor,color2:RGBColor,probability:float) -> list:
    """
    Sets timings for a layer
    :param input: The device to set the timings for
    :param layers: [layer_1_base, layer_1_target, layer_1_timing, layer_1_current]
    :param timing_low: The low timing of the layer
    :param timing_high: The high timing of the layer
    :param color1: The base color to set
    :param color2: The second color to set
    :param probability: The probability of setting a color
    :return: The layers used as input
    """

    if layers[3][0] is None:
        random_timings = [random.randint(timing_low, timing_high) for _ in layers[3]]
        layers[3][:] = random_timings
        layers[2][:] = random_timings
    else:
        for zone in device.zones:
            for led in zone.leds:
                layers[2][led.id] -= 1
                if layers[2][led.id] == 0:
                    random_timing = random.randint(timing_low, timing_high)
                    layers[3][led.id] = random_timing
                    layers[2][led.id] = random_timing
                    layers[0][led.id] = layers[1][led.id]
                    layers[1][led.id] = set_random_color(color1, color2, probability)
    return layers

def gradient(device, layer_1_base: list, layer_1_target: list, layer_1_timing: list, layer_1_current: list) -> list:
    """
    Sets the gradient for a layer
    :param device: The device to set the gradient for
    :param layer_1_base: The base color of the layer
    :param layer_1_target: The target color of the layer
    :param layer_1_timing: The timing of the layer
    :param layer_1_current: The current timing of the layer
    :return: The gradient of the layer
    """
    
    def get_gradient_percentage(current_timing: int, timing: int):
        if timing == 0:
            return 0
        else:
            return (timing / current_timing) * 100
    
    def calculations(r1: int, g1: int, b1: int, r2: int, g2: int, b2: int, gradient_percentage: float) -> RGBColor:
        r, g, b = numpy.array([r2, g2, b2]) * (100 - gradient_percentage) + numpy.array([r1, g1, b1]) * gradient_percentage
        return RGBColor((r / 100).astype(int), (g / 100).astype(int), (b / 100).astype(int))
    
    layer_1_final = []
    for i in device.zones:
        for j in i.leds:
            if layer_1_current[j.id] == layer_1_timing[j.id]:
                layer_1_final.append(layer_1_base[j.id])
            else:                
                r1, g1, b1 = layer_1_base[j.id].red, layer_1_base[j.id].green, layer_1_base[j.id].blue
                r2, g2, b2 = layer_1_target[j.id].red, layer_1_target[j.id].green, layer_1_target[j.id].blue

                layer_1_final.append(calculations(r1, g1, b1, r2, g2, b2, get_gradient_percentage(layer_1_current[j.id], layer_1_timing[j.id])))
    
    return layer_1_final
    
def set_volume(device, color1: RGBColor, color2: RGBColor) -> list:
    
    def volume_gradient(percent) -> RGBColor:
        colora = [color1.red, color1.green, color1.blue]
        colorb = [color2.red, color2.green, color2.blue]
        return RGBColor(int(colora[0] * (1 - percent) + colorb[0] * percent), int(colora[1] * (1 - percent) + colorb[1] * percent), int(colora[2] * (1 - percent) + colorb[2] * percent))

    colors = []
    for i in range(len(device.leds)):
        colors.append(None)

    for i in device.zones:
        led_id = i.leds[0].id+1
        size = len(i.leds)-2
        for i in range(size):
            displayed_volume = size*volume
            if i < int(displayed_volume):
                colors[led_id + i] = RGBColor(255, 255, 255)
            else:
                colors[led_id + i] = volume_gradient(displayed_volume-i)
                break

    return colors