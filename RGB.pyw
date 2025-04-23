from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import time
from effects.Base import *
import colorsys

brightness_final = 50
color_2_percentage = 0.2
gradient_min_steps = 4
gradient_max_steps = 6
updates_per_second = 30
devices_layers: dict = {}
names = ["Corsair Vengeance Pro RGB", "MSI MPG B550 GAMING PLUS (MS-7C56)"]
layer_names = [
    "layer_1_base",  # * ID 0
    "layer_1_target",  # * ID 1
    "layer_1_timing",  # * ID 2
    "layer_1_current",  # * ID 3
    "layer_1_final",  # * ID 4
    "layer_2_volume",  # * ID 5
]


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

    def get_color(self, hue_correction: float = 0.0, saturation_correction: float = 0.0, brightness_correction: float = 0.0) -> RGBColor:
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


purple = Color()
purple.set_HSV(255, 255, brightness_final)
white = Color()
white.set_HSV(0, 0, brightness_final)
colors = [purple, white]


def startup() -> OpenRGBClient:
    """
    Starts the OpenRGB Client
    :return: The client
    :global: devices
    """

    while True:
        try:
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
                for j in layer_names:
                    devices_layers[device.id][j] = []
                    for led in device.leds:
                        devices_layers[device.id][j].append(None)
            return client
        except:
            time.sleep(.1)


def brightness_adjust(color: RGBColor, brightness) -> RGBColor:
    """
    Adjusts the brightness of a color
    :param color: The color to adjust
    :return: The adjusted color
    """
    return RGBColor(int(color.red * brightness),
                    int(color.green * brightness),
                    int(color.blue * brightness))


def update_effects(device) -> None:
    if any(zone.name == "JRAINBOW2" for zone in device.zones):
        color1 = colors[0].get_color(hue_correction=5)
        color2 = colors[1].get_color()
    else:
        color1 = colors[0].get_color()
        color2 = colors[1].get_color()

    if devices_layers[device.id][layer_names[0]][0] is None:
        devices_layers[device.id][layer_names[0]
                                  ] = set_base_color(device, color1)

    if devices_layers[device.id][layer_names[1]][0] is None:
        devices_layers[device.id][layer_names[1]] = set_random_colors(
            device, color1, color2, color_2_percentage)

    devices_layers[device.id][tuple(layer_names[:5])] = \
        set_timings(device,
                    [devices_layers[device.id][ln]
                     for ln in layer_names[:5]],
                    gradient_min_steps, gradient_max_steps, color1, color2, color_2_percentage)

    devices_layers[device.id][layer_names[4]] = gradient(
        device, [devices_layers[device.id][ln] for ln in layer_names[:4]])

    if device.name == names[1]:
        devices_layers[device.id][layer_names[4]][0] = color1
    if device.name == names[0]:
        devices_layers[device.id][layer_names[5]
                                  ] = set_volume(device, color1, color2)


def apply_layers(device) -> None:
    """
    Mixes the colors of each layer and applies them
    :param input: The device to set the colors for
    """

    if devices_layers[device.id][layer_names[4]][0] is not None:
        colors = devices_layers[device.id][layer_names[4]]

        if device.name == names[0]:
            for i in range(len(device.colors)):
                if devices_layers[device.id][layer_names[5]][i] is not None:
                    colors[i] = devices_layers[device.id][layer_names[5]][i]

        device.set_colors(colors, True)


def main():
    startup()

    start = time.time()
    delay = 0
    desired_delay = 1/(updates_per_second)

    while True:
        try:
            if delay > desired_delay:

                start = time.time()
                for device in devices:
                    update_effects(device)
                    apply_layers(device)

            time.sleep(1/240)
            delay = time.time() - start
        except ConnectionAbortedError:
            startup()


if __name__ == "__main__":
    update_volume()
    main()
