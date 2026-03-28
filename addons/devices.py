from ctypes.wintypes import RGB
import random

from numpy import outer
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
            "layer_1_volume",  # * ID 5
            ]
        self.last_volume = {}  # Track per-device to fix multiple devices with same name
                 
    def set_layer(self, device, layer_name: str, layer: list) -> None:
        self.devices_layers[device.id][layer_name] = layer

    def _apply_correction(self, color: RGBColor, hue: float, sat: float, bright: float) -> RGBColor:
        if color is None:
            return None
        return RGBColor(
            int((color.red + hue) % 256),
            int(max(0, min(255, color.green + sat))),
            int(max(0, min(255, color.blue + bright))),
        )

    def _get_corrections_for_position(self, device, position: int) -> list:
        """Get all corrections that apply to a specific LED position."""
        records = self.color_corrections.get(device.id, [])
        applicable = []
        
        for pos, zidx, zname, hue, sat, bright in records:
            if pos == position:
                applicable.append((hue, sat, bright))
            elif pos is None:
                try:
                    zone = self._get_zone(device, zidx, zname)
                    for led in zone.leds:
                        if led.id == position:
                            applicable.append((hue, sat, bright))
                            break
                except ValueError:
                    pass
        
        return applicable

    def _apply_all_corrections_to_color(self, device, color: RGBColor, position: int) -> RGBColor:
        """Apply all corrections for a specific LED position."""
        for hue, sat, bright in self._get_corrections_for_position(device, position):
            color = self._apply_correction(color, hue, sat, bright)
        return color

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

        
    def set_color_correction(self, device, position=None, zone_index=None, zone_name=None,
                        hue_correction=0.0, saturation_correction=0.0, brightness_correction=0.0):
        """Register a colour correction. Exactly one of position, zone_index, or zone_name must be provided."""
        if sum([position is not None, zone_index is not None, zone_name is not None]) != 1:
            raise ValueError("must specify exactly one of position, zone_index or zone_name")
        
        record = (position, zone_index, zone_name, hue_correction, saturation_correction, brightness_correction)
        self.color_corrections.setdefault(device.id, []).append(record)
                
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
        
        # Apply color corrections to the final gradient layer
        final_layer = self.get_layer(device, self.layer_names[4])
        corrected_layer = [
            self._apply_all_corrections_to_color(device, color, i) if color is not None else None
            for i, color in enumerate(final_layer)
        ]
        self.set_layer(device, self.layer_names[4], corrected_layer)
        
    def set_color_final(self, device, color: RGBColor, position: int) -> None:
        """Sets the final color for a specific LED in the final layer with corrections applied
        :param device: The device to set the color for
        :param color: The color to set
        :param position: The ID of the LED to set the color for"""
        
        corrected_color = self._apply_all_corrections_to_color(device, color, position)
        layer = self.get_layer(device, self.layer_names[4])
        layer[position] = corrected_color
        self.set_layer(device, self.layer_names[4], layer)
        
    def set_volume(self, device, volume) -> None:
        """Sets the volume for a specific LED in the final layer
        :param device: The device to set the color for
        :param volume: The volume to set (0.0 to 1.0)"""
        
        last_vol = self.last_volume.get(device.id, -1)  # Use -1 as initial default
        if volume != last_vol:
            color1, color2, _ = self.get_colors(device)
            volume_colors = set_volume(device, color1, color2, volume)
            self.last_volume[device.id] = volume
            output=[]
            for i in range(len(device.leds)):
                if volume_colors[i] is not None:
                    output.append(volume_colors[i])
                else:
                    output.append(None)
            self.set_layer(device, self.layer_names[5], output)
                    
    def apply_final_layer(self, device) -> None:
        output = self.get_layer(device, self.layer_names[4])
        if self.get_layer(device, self.layer_names[5]) is not None:
            volume_layer = self.get_layer(device, self.layer_names[5])
            for i in range(len(device.leds)):
                if volume_layer[i] is not None:
                    output[i] = volume_layer[i]
            
        device.colors = output
