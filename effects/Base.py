import random
from turtle import color
import psutil
import comtypes
import threading
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

def set_base_color(device, color) -> list:
    """
    Sets the base color for a layer
    :param input: The device to set the colors for
    :param color: The color to set
    """

    colors = []
    for i in device.zones:
        for _ in i.leds:
            colors.append(color)
    return colors

def set_random_color(color1, color2, probability) -> list:
    """
    Sets random color for a led
    :param input: The device to set the colors for
    :param color1: The base color to set
    :param color2: The second color to set
    :param probability: The probability of setting a color
    """
    
    color = []
    
    if random.random() < probability:
        color = color2
    else:
        color = color1

    return color

def set_random_colors(device, color1, color2, probability) -> list:
    """
    Sets random colors for a layer
    :param input: The device to set the colors for
    :param color1: The base color to set
    :param color2: The second color to set
    :param probability: The probability of setting a color
    """
    
    layer = []
    
    for i in device.zones:
        for _ in i.leds:
            layer.append(set_random_color(color1, color2, probability))

    return layer

def set_timings(device, layers, timing_low, timing_high,color1, color2, probability) -> list:
    """
    Sets timings for a layer
    :param input: The device to set the timings for
    :param layers: [layer_1_base, layer_1_target, layer_1_timing, layer_1_current]
    :param timing_low: The low timing of the layer
    :param timing_high: The high timing of the layer
    """

    if layers[3][0] is None:
        for i in range(len(layers[3])):
            layers[3][i] = random.randint(timing_low, timing_high)
            layers[2][i] = layers[3][i]
    else:
        for zone in device.zones:
            for led in zone.leds:
                layers[2][led.id] -= 1
                if layers[2][led.id] == 0:
                    layers[3][led.id] = random.randint(timing_low, timing_high)
                    layers[2][led.id] = layers[3][led.id]
                    layers[0][led.id] = layers[1][led.id]
                    layers[1][led.id] = set_random_color(color1, color2, probability)
    return layers

def gradient(input, layer_1_base, layer_1_target, layer_1_timing, layer_1_current) -> list:
    layer_1_final = []
    
    def get_gradient_percentage(current_timing, timing):
        if timing == 0:
            gradient_percentage = 0
        else:
            gradient_percentage = (timing / current_timing) * 100
        return gradient_percentage
    
    for i in input.zones:
        for j in i.leds:
            if layer_1_current[j.id] == layer_1_timing[j.id]:
                layer_1_final.append(layer_1_base[j.id])
            else:
                gradient_percentage = get_gradient_percentage(layer_1_current[j.id], layer_1_timing[j.id])
                
                r1, g1, b1 = layer_1_base[j.id].red, layer_1_base[j.id].green, layer_1_base[j.id].blue
                r2, g2, b2 = layer_1_target[j.id].red, layer_1_target[j.id].green, layer_1_target[j.id].blue

                r = int((r2 * (100 - gradient_percentage) + r1 * gradient_percentage) / 100)
                g = int((g2 * (100 - gradient_percentage) + g1 * gradient_percentage) / 100)
                b = int((b2 * (100 - gradient_percentage) + b1 * gradient_percentage) / 100)
                
                layer_1_final.append(RGBColor(r, g, b))
    
    return layer_1_final
    
def set_volume(device, color1, color2) -> list:
    
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