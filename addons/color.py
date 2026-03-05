import colorsys
from openrgb.utils import RGBColor

class Color():
    def __init__(self, red: int = 0, green: int = 0, blue: int = 0) -> None:
        """Initialize color from RGB values, stored internally as HSL."""
        self.set_rgb(red, green, blue)

    def _rgb_to_hsl(self, red: int, green: int, blue: int) -> tuple:
        """Convert RGB values to HSL."""
        h, l, s = colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)
        return h * 360.0, s * 100.0, l * 100.0

    def _hsl_to_rgb(self, hue: float, saturation: float, lightness: float) -> tuple:
        """Convert HSL values to RGB."""
        h = hue / 360.0
        s = saturation / 100.0
        l = lightness / 100.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)

    def _hsl_to_hsv(self, hue: float, saturation: float, lightness: float) -> tuple:
        """Convert HSL values to HSV."""
        s = saturation / 100.0
        l = lightness / 100.0
        v = l + s * min(l, 1 - l)
        s_hsv = 0 if v == 0 else 2 * (1 - l / v)
        # Return HSV with hue as-is and saturation/value in 0-100 scale
        return hue, s_hsv * 100.0, v * 100.0

    def set_hsl(self, hue: float, saturation: float, lightness: float) -> None:
        """
        Sets the color using HSL values.
        :param hue: Hue value (0 to 360)
        :param saturation: Saturation value (0 to 100)
        :param lightness: Lightness value (0 to 100)
        """
        self.hue = hue % 360.0
        self.saturation = max(0.0, min(100.0, saturation))
        self.lightness = max(0.0, min(100.0, lightness))

    def set_rgb(self, red: int, green: int, blue: int) -> None:
        """Set the color using RGB values, storing internally as HSL."""
        self.hue, self.saturation, self.lightness = self._rgb_to_hsl(red, green, blue)

    def set_hex(self, hex_color: str) -> None:
        """
        Sets the color using a hex color string.
        :param hex_color: Hex color value (e.g., "#FF5733" or "FF5733")
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("Hex color must be 6 characters long")
        red = int(hex_color[0:2], 16)
        green = int(hex_color[2:4], 16)
        blue = int(hex_color[4:6], 16)
        self.set_rgb(red, green, blue)

    def brightness_set(self, brightness: float) -> None:
        """
        Adjusts the brightness of the color.
        :param brightness: Brightness value (0 to 100)
        """
        self.lightness = max(0.0, min(100.0, brightness))

    def get_color_mix(self, color, percentage: float) -> RGBColor:
        """
        Mixes the color with another RGBColor object based on the percentage.
        :param color: The RGBColor object to mix with
        :param percentage: The percentage to mix (0.0 to 1.0)
        :return: The mixed color as a RGBColor object
        """
        h, s, v = self._hsl_to_hsv(self.hue, self.saturation, self.lightness)
        current_color = RGBColor.fromHSV(h, s, v)
        r = int(current_color.red * percentage + color.red * (1 - percentage))
        g = int(current_color.green * percentage + color.green * (1 - percentage))
        b = int(current_color.blue * percentage + color.blue * (1 - percentage))
        return RGBColor(r, g, b)

    def get_color(self, hue_correction: float = 0.0, saturation_correction: float = 0.0, brightness_correction: float = 0.0) -> RGBColor:
        """
        Returns the color as a RGBColor object with applied corrections
        :param hue_correction: The amount to adjust the hue (-360.0 to 360.0)
        :param saturation_correction: The amount to adjust the saturation (-100.0 to 100.0)
        :param brightness_correction: The amount to adjust the brightness (-100.0 to 100.0)
        :return: The color as a corrected RGBColor object
        """
        hue = (self.hue + hue_correction) % 360.0
        saturation = max(0.0, min(100.0, self.saturation + saturation_correction))
        lightness = max(0.0, min(100.0, self.lightness + brightness_correction))
        h, s, v = self._hsl_to_hsv(hue, saturation, lightness)
        return RGBColor.fromHSV(h, s, v)

    @property
    def red(self) -> int:
        """Get the red component of the color (0-255)."""
        r, _, _ = self._hsl_to_rgb(self.hue, self.saturation, self.lightness)
        return r

    @property
    def green(self) -> int:
        """Get the green component of the color (0-255)."""
        _, g, _ = self._hsl_to_rgb(self.hue, self.saturation, self.lightness)
        return g

    @property
    def blue(self) -> int:
        """Get the blue component of the color (0-255)."""
        _, _, b = self._hsl_to_rgb(self.hue, self.saturation, self.lightness)
        return b

