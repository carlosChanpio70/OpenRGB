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

def set_base_color(input, color) -> list:
    """
    Sets the base color for a layer
    :param input: The device to set the colors for
    :param color: The color to set
    """

    colors = []
    for i in input.zones:
        for _ in i.leds:
            colors.append(color)
    return colors

def set_random_color(input, color, layer, probability) -> list:
    """
    Sets random color for a layer
    :param input: The device to set the colors for
    :param color: The color to set
    :param layer: The layer to set the colors for
    :param probability: The probability of setting a color
    """
    
    colors = []
    
    for i in input.zones:
        for _ in i.leds:
            if random.random() < probability:
                colors.append(color)
            else:
                colors.append(0)

    for i in range(len(colors)):
        if colors[i] == color:
            layer[i] = color

    return layer

def gradient(input, color, color_layer, current_timing, timing_layer) -> list:
    
    gradient_layer = []

    for i in input.zones:
        for j in i.leds:
            if current_timing[j.id] == timing_layer[j.id]:
                gradient_layer.append(color)
            else:
                gradient_percentage = current_timing[j.id] / timing_layer[j.id]
                gradient_layer.append(int(color_layer[j.id] * (1 - gradient_percentage) + color * gradient_percentage))
    return gradient_layer
    
def check_timing(input, current_timing, timing_layer, timing_low, timing_high):
    for i in input.zones:
        for j in i.leds:
            if current_timing[j.id] == timing_layer[j.id]:
                current_timing[j.id] = 0
                timing_layer[j.id] = random.randint(timing_low, timing_high)
                
    return current_timing, timing_layer

def set_volume(input, name) -> list:
    
    def volume_gradient(percent) -> RGBColor:
        color1 = [50, 0, 255]
        color2 = [255, 255, 255]
        return RGBColor(int(color1[0] * (1 - percent) + color2[0] * percent), int(color1[1] * (1 - percent) + color2[1] * percent), int(color1[2] * (1 - percent) + color2[2] * percent))

    if input.name == name:
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
                    colors[led_id + i] = volume_gradient(displayed_volume-i)
                    break

    return colors