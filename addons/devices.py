import random
from addons.effects import set_random_color, set_random_colors, set_base_color, set_volume, RGBColor


class Devices:
    def __init__(self,) -> None:
        self.device_list = []
        self.devices_layers = {}
        self.colors = {}
        self.color_corrections = {}
        self.layer_names = [
            "layer_1_base",  # * ID 0
            "layer_1_target",  # * ID 1
            "layer_1_timing",  # * ID 2
            "layer_1_current",  # * ID 3
            "layer_1_final",  # * ID 4
            "layer_2_volume",  # * ID 5
            ]
        self.last_volume = 0.0
                 
    def set_layer(self, device, layer_name: str, layer: list) -> None:
        # apply all stored colour corrections to any layer being written.
        # this ensures that every time a layer is updated the adjustments for
        # colour[0] are persisted, regardless of which layer is modified.
        self._apply_corrections_to_layer(device, layer)
        self.devices_layers[device.id][layer_name] = layer
        
    def set_color_final(self, device, color: RGBColor, position: int) -> None:
        """Sets the final color for a specific LED in the final layer
        :param device: The device to set the color for
        :param color_id: The ID of the color to set (0 or 1)
        :param position: The ID of the LED to set the color for"""
        
        layer = self.get_layer(device, self.layer_names[4])
        layer[position] = color
        self.set_layer(device, self.layer_names[4], layer)

    def _apply_correction(self, color: RGBColor, hue: float, sat: float, bright: float) -> RGBColor:
        if color is None:
            return None
        return RGBColor(
            int((color.red + hue) % 256),
            int(max(0, min(255, color.green + sat))),
            int(max(0, min(255, color.blue + bright))),
        )

    def _get_zone(self, device, zone_index=None, zone_name=None):
        """Resolve zone by index or name. Raises ValueError if not found."""
        if zone_index is not None:
            try:
                return device.zones[zone_index]
            except (IndexError, AttributeError):
                raise ValueError(f"invalid zone_index: {zone_index}")
        zone = next((z for z in getattr(device, "zones", []) if getattr(z, "name", None) == zone_name), None)
        if zone is None:
            raise ValueError(f"invalid zone_name: {zone_name}")
        return zone

    def _apply_corrections_to_layer(self, device, layer, records=None):
        """Apply one or more correction records to *layer* in place."""
        if records is None:
            records = self.color_corrections.get(device.id, [])

        for pos, zidx, zname, hue, sat, bright in records:
            if pos is not None:
                layer[pos] = self._apply_correction(layer[pos], hue, sat, bright)
            else:
                zone = self._get_zone(device, zidx, zname)
                for led in zone.leds:
                    layer[led.id] = self._apply_correction(layer[led.id], hue, sat, bright)

        
    def set_color_correction(self, device, position=None, zone_index=None, zone_name=None,
                        hue_correction=0.0, saturation_correction=0.0, brightness_correction=0.0):
        """Register a colour correction. Exactly one of position, zone_index, or zone_name must be provided."""
        if sum([position is not None, zone_index is not None, zone_name is not None]) != 1:
            raise ValueError("must specify exactly one of position, zone_index or zone_name")
        
        record = (position, zone_index, zone_name, hue_correction, saturation_correction, brightness_correction)
        self.color_corrections.setdefault(device.id, []).append(record)
        
        if device in self.device_list:
            for ln in self.layer_names[:2]:
                self.set_layer(device, ln, self.get_layer(device, ln))
                
    def get_colors(self, device) -> dict:
        return self.colors[device.id]
                
    def get_layer_names(self) -> list:
        return self.layer_names
    
    def get_layer(self, device, layer_name: str) -> list:
        return self.devices_layers[device.id][layer_name]
    
    def get_device(self) -> list:
        return self.device_list
    
    def add_device(self, device, color1, color2, color_2_percentage) -> None:
        layers = {layer: [None] * len(device.leds) for layer in self.layer_names}
        base = set_base_color(device, color1)
        target = set_random_colors(device, color1, color2, color_2_percentage)
        
        layers[self.layer_names[0]] = base
        layers[self.layer_names[1]] = target
        self.device_list.append(device)
        self.devices_layers[device.id] = layers
        self.colors[device.id] = [color1, color2, color_2_percentage]
        
        self.set_layer(device, self.layer_names[0], base)
        self.set_layer(device, self.layer_names[1], target)
        
    def gradient(self, device) -> None:
        """Sets the gradient for a layer"""
        def calculate_gradient(c1: RGBColor, c2: RGBColor, pct: float) -> RGBColor:
            if c1 == c2:
                return c1
            f = pct / 100
            return RGBColor(
                int(c1.red * f + c2.red * (1 - f)),
                int(c1.green * f + c2.green * (1 - f)),
                int(c1.blue * f + c2.blue * (1 - f))
            )

        base, target, timing, current = [self.get_layer(device, ln) for ln in self.layer_names[:4]]
        
        gradient_layer = [
            base[led.id] if current[led.id] == timing[led.id]
            else calculate_gradient(
                base[led.id], target[led.id],
                100 * (timing[led.id] / current[led.id])
            )
            for zone in device.zones for led in zone.leds
        ]
        self.set_layer(device, self.layer_names[4], gradient_layer)

    def set_timings(self, device, min_steps: int, max_steps: int) -> None:
        base, target, timing, current = [self.get_layer(device, ln) for ln in self.layer_names[:4]]
        color1, color2, color_2_percentage = self.get_colors(device)

        if current[0] is None:
            random_timings = [random.randint(min_steps, max_steps) for _ in current]
            current[:] = random_timings
            timing[:] = random_timings[:]
        else:
            for zone in device.zones:
                for led in zone.leds:
                    timing[led.id] -= 1
                    if timing[led.id] < 0:
                        new_timing = random.randint(min_steps, max_steps)
                        current[led.id] = new_timing
                        timing[led.id] = new_timing
                        base[led.id] = target[led.id]
                        target[led.id] = set_random_color(color1, color2, color_2_percentage)

        for i, layer in enumerate([base, target, timing, current]):
            if self.get_layer(device, self.layer_names[i]) != layer:
                self.set_layer(device, self.layer_names[i], layer)

    def set_gradient(self, device, gradient_min_steps: int, gradient_max_steps: int) -> None:
        self.set_timings(device, gradient_min_steps, gradient_max_steps)
        self.gradient(device)
        
    def set_volume(self, device, volume) -> None:
        if volume != self.last_volume:
            color1, color2, _ = self.get_colors(device)
            self.set_layer(device, self.layer_names[5],set_volume(device, color1, color2, volume))
            self.last_volume = volume
