import colorsys
from openrgb.utils import RGBColor

class Color():
    def __init__(self, red: int = 0, green: int = 0, blue: int = 0) -> None:
        self.red = red
        self.green = green
        self.blue = blue

    def set_HSV(self, hue: float, saturation: float, brightness: float) -> None:
        """
        Sets the color using HSV values.
        :param hue: Hue value (0 to 360)
        :param saturation: Saturation value (0 to 255)
        :param brightness: Brightness value (0 to 100)
        """
        hue = hue / 360.0  # Convert hue to range [0, 1]
        saturation = saturation / 255.0  # Convert saturation to range [0, 1]
        brightness = brightness / 100.0  # Convert brightness to range [0, 1]
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
        self.red = int(r * 255)
        self.green = int(g * 255)
        self.blue = int(b * 255)

    def set_RGB(self, red: int, green: int, blue: int) -> None:
        self.red = red
        self.green = green
        self.blue = blue

    def brightness_set(self, brightness: float) -> None:
        """
        Adjusts the brightness of the color.
        :param brightness: Brightness value (0 to 100)
        """
        brightness = max(0.0, min(100.0, brightness)
                         )  # Clamp brightness to [0, 100]
        hue, saturation, _ = colorsys.rgb_to_hsv(
            self.red / 255, self.green / 255, self.blue / 255)
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness / 100.0)
        self.red = int(r * 255)
        self.green = int(g * 255)
        self.blue = int(b * 255)

    def getColor_mix(self, color, percentage: float) -> RGBColor:
        """
        Mixes the color with another RGBColor object based on the percentage.
        :param color: The RGBColor object to mix with
        :param percentage: The percentage to mix (0.0 to 1.0)
        :return: The mixed color as a RGBColor object
        """
        r = int(self.red * percentage + color.red * (1 - percentage))
        g = int(self.green * percentage + color.green * (1 - percentage))
        b = int(self.blue * percentage + color.blue * (1 - percentage))
        return RGBColor(r, g, b)

    def getColor(self, hue_correction: float = 0.0, saturation_correction: float = 0.0, brightness_correction: float = 0.0) -> RGBColor:
        """
        Returns the color as a RGBColor object with applied corrections
        :param hue_correction: The amount to adjust the hue (-360.0 to 360.0)
        :param saturation_correction: The amount to adjust the saturation (-255.0 to 255.0)
        :param brightness_correction: The amount to adjust the brightness (-100.0 to 100.0)
        :return: The color as a corrected RGBColor object
        """
        hue, saturation, brightness = colorsys.rgb_to_hsv(
            self.red / 255, self.green / 255, self.blue / 255)
        hue = ((hue * 360.0 + hue_correction) % 360.0) / \
            360.0  # Adjust hue and normalize to [0, 1]
        # Adjust and clamp saturation
        saturation = max(
            0.0, min(1.0, (saturation * 255.0 + saturation_correction) / 255.0))
        # Adjust and clamp brightness
        brightness = max(
            0.0, min(1.0, (brightness * 100.0 + brightness_correction) / 100.0))
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
        return RGBColor(int(r * 255), int(g * 255), int(b * 255))
