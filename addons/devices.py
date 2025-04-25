from addons.effects import *


class Devices:
    def __init__(self,) -> None:
        self.devices = []
        self.devices_layers = {}
        self.colors = {}
        self.layer_names = [
            "layer_1_base",  # * ID 0
            "layer_1_target",  # * ID 1
            "layer_1_timing",  # * ID 2
            "layer_1_current",  # * ID 3
            "layer_1_final",  # * ID 4
            "layer_2_volume",  # * ID 5
            ]
                 
    def setLayer(self, device, layer_name: str, layer: list) -> None:
        self.devices_layers[device.id][layer_name] = layer
        
    def setColorFinal(self, device, color_id: int, position: int) -> None:
        layer = self.getLayer(device, self.layer_names[4])
        layer[position] = self.getColors(device)[color_id]
        self.setLayer(device, self.layer_names[4], layer)
                
    def getColors(self, device) -> dict:
        return self.colors[device.id]
                
    def get_layer_names(self) -> list:
        return self.layer_names
    
    def getLayer(self, device, layer_name: str) -> list:
        return self.devices_layers[device.id][layer_name]
    
    def getDevices(self) -> list:
        return self.devices
    
    def addDevice(self, device, color1, color2, color_2_percentage) -> None:
        self.devices.append(device)
        self.devices_layers[device.id] = {layer: [None] * len(device.leds) for layer in self.layer_names}
        self.colors[device.id] = [color1, color2, color_2_percentage]
        
        self.setLayer(device, self.layer_names[0], set_base_color(device, color1))
        self.setLayer(device, self.layer_names[1], set_random_colors(device, color1, color2, color_2_percentage))
        
    def gradient(self, device) -> None:
        """
        Sets the gradient for a layer
        :param device: The device to set the gradient for
        """
        def calculate_gradient(color1: RGBColor, color2: RGBColor, percentage: float) -> RGBColor:
            factor = percentage / 100
            return RGBColor(
                int(color1.red * factor + color2.red * (1 - factor)),
                int(color1.green * factor + color2.green * (1 - factor)),
                int(color1.blue * factor + color2.blue * (1 - factor))
            )

        get_percentage_cached = lambda start, end: 100 * (start / end) if end != 0 else 0

        layers = [self.getLayer(device, ln) for ln in self.layer_names[:4]]
        gradient_layer = [
            layers[0][led.id] if layers[3][led.id] == layers[2][led.id]
            else calculate_gradient(
                layers[0][led.id],
                layers[1][led.id],
                get_percentage_cached(layers[2][led.id], layers[3][led.id])
            )
            for zone in device.zones for led in zone.leds
        ]

        self.setLayer(device, self.layer_names[4], gradient_layer)

    def set_timings(self, device, min_steps: int, max_steps: int) -> None:
        layer_base = self.getLayer(device, self.layer_names[0])
        layer_target = self.getLayer(device, self.layer_names[1])
        layer_timing = self.getLayer(device, self.layer_names[2])
        layer_current = self.getLayer(device, self.layer_names[3])
        color1, color2, color_2_percentage = self.getColors(device)

        if layer_current[0] is None:
            random_timings = [random.randint(min_steps, max_steps) for _ in layer_current]
            layer_current[:] = random_timings
            layer_timing[:] = random_timings[:]
        else:
            for zone in device.zones:
                for led in zone.leds:
                    led_id = led.id
                    layer_timing[led_id] -= 1
                    if layer_timing[led_id] < 0:
                        new_timing = random.randint(min_steps, max_steps)
                        layer_current[led_id] = new_timing
                        layer_timing[led_id] = new_timing
                        layer_base[led_id] = layer_target[led_id]
                        layer_target[led_id] = set_random_color(color1, color2, color_2_percentage)

        if self.getLayer(device, self.layer_names[0]) != layer_base:
            self.setLayer(device, self.layer_names[0], layer_base)
        if self.getLayer(device, self.layer_names[1]) != layer_target:
            self.setLayer(device, self.layer_names[1], layer_target)
        if self.getLayer(device, self.layer_names[2]) != layer_timing:
            self.setLayer(device, self.layer_names[2], layer_timing)
        if self.getLayer(device, self.layer_names[3]) != layer_current:
            self.setLayer(device, self.layer_names[3], layer_current)

    def setGradient(self, device, gradient_min_steps: int, gradient_max_steps: int) -> None:
        self.set_timings(device, gradient_min_steps, gradient_max_steps)
        self.gradient(device)
        
    def setVolume(self, device) -> None:
        color1, color2, _ = self.getColors(device)
        self.setLayer(device, self.layer_names[5],
                     set_volume(device, color1, color2))
