from operator import ge
import random
import psutil
import comtypes
import threading
from openrgb.utils import RGBColor
import time
import numpy
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

def get_percentage(value1: float, value2: float) -> float:
    if value1 == 0:
        return 0
    else:
        return (value1 / value2) * 100

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
        layers[3][:] = [random.randint(timing_low, timing_high) for _ in layers[3]]
        layers[2][:] = layers[3][:]
    else:
        for zone in device.zones:
            for led in zone.leds:
                layers[2][led.id] -= 1
                if layers[2][led.id] < 0:
                    layers[3][led.id] = random.randint(timing_low, timing_high)
                    layers[2][led.id] = layers[3][led.id]
                    layers[0][led.id] = layers[1][led.id]
                    layers[1][led.id] = set_random_color(color1, color2, probability)
    return layers

def gradient(device,layers: list) -> list:
    """
    Sets the gradient for a layer
    :param device: The device to set the gradient for
    :param layers: [layer_1_base, layer_1_target, layer_1_timing, layer_1_current]
    :return: The gradient of the layer
    """
    
    def calculations(color1: RGBColor, color2: RGBColor, gradient_percentage: float) -> RGBColor:
        r, g, b = numpy.array([color2.red, color2.green, color2.blue]) * (100 - gradient_percentage) + numpy.array([color1.red, color1.green, color1.blue]) * gradient_percentage
        return RGBColor(int(r / 100), int(g / 100), int(b / 100))
    
    layer_1_final = []
    for i in device.zones:
        for j in i.leds:
            if layers[3][j.id] == layers[2][j.id]:
                layer_1_final.append(layers[0][j.id])
            else:                
                layer_1_final.append(calculations(layers[0][j.id], layers[1][j.id], get_percentage(layers[2][j.id], layers[3][j.id])))
    
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