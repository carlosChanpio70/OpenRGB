import random
from typing import List, Optional
from openrgb.utils import RGBColor

def interpolate_alpha(color1: RGBColor, color2: RGBColor, progress: float) -> float:
    alpha1 = getattr(color1, "alpha", 1.0)
    alpha2 = getattr(color2, "alpha", 1.0)
    return alpha1 * (1 - progress) + alpha2 * progress

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
    
def set_volume(device, color1: RGBColor, color2: RGBColor, volume) -> list:
    volume = max(0.0, min(1.0, float(volume)))
    if volume <= 0.001:
        return [None] * len(device.leds)

    colors: List[Optional[RGBColor]] = [None] * len(device.leds)

    def volume_gradient(percent: float) -> RGBColor:
        color = RGBColor(255, 255, 255)
        setattr(color, "alpha", interpolate_alpha(color1, color2, percent))
        return color

    for zone in device.zones:
        leds = zone.leds[1:-1]
        size = len(leds)
        displayed_volume = size * volume
        filled_leds = int(displayed_volume)
        for position, led in enumerate(leds):
            if position < filled_leds:
                color = RGBColor(255, 255, 255)
                setattr(color, "alpha", getattr(color1, "alpha", 1.0))
                colors[led.id] = color
            elif position == filled_leds and displayed_volume > filled_leds:
                colors[led.id] = volume_gradient(displayed_volume - filled_leds)
            else:
                break

    return colors