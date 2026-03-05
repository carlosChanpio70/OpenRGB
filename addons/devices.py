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
        """Return a new RGBColor with the given adjustments applied.

        Hue is wrapped around 0–255, while saturation/brightness are clamped to
        the valid range.  This logic mirrors the old implementation in
        :meth:`set_color_correction`.
        """
        if color is None:
            return None
        return RGBColor(
            int((color.red + hue) % 256),
            int(max(0, min(255, color.green + sat))),
            int(max(0, min(255, color.blue + bright))),
        )

    def _apply_corrections_to_layer(self, device, layer, records=None):
        """Apply one or more correction records to *layer* in place.

        The *records* parameter should be an iterable of tuples
        ``(position, zone_index, zone_name, hue, sat, bright)``.  If omitted,
        all stored corrections for the device are applied.  The corrections are
        applied relative to the *current* colour values in *layer*, which allows
        them to persist even when the layer is later mutated.
        """
        if records is None:
            records = self.color_corrections.get(device.id, [])

        for pos, zidx, zname, hue, sat, bright in records:
            if pos is not None:
                layer[pos] = self._apply_correction(layer[pos], hue, sat, bright)
            else:
                zone = None
                if zidx is not None:
                    try:
                        zone = device.zones[zidx]
                    except (IndexError, AttributeError):
                        raise ValueError(f"invalid zone_index: {zidx}")
                else:
                    zone = next((z for z in getattr(device, "zones", []) if getattr(z, "name", None) == zname), None)
                    if zone is None:
                        raise ValueError(f"invalid zone_name: {zname}")
                for led in zone.leds:
                    layer[led.id] = self._apply_correction(layer[led.id], hue, sat, bright)

        
    def set_color_correction(
        self,
        device,
        position: int | None = None,
        zone_index: int | None = None,
        zone_name: str | None = None,
        hue_correction: float = 0.0,
        saturation_correction: float = 0.0,
        brightness_correction: float = 0.0,
    ) -> None:
        """Register a colour correction for the given device.

        The correction is applied a single time.  If the device has not yet
        been added it is queued and consumed when ``add_device`` runs.  If the
        device already exists the adjustment is performed immediately by
        rebuilding/re‑writing the base layer; this means there is no longer any
        requirement for the correction to occur "before" the device is added.
        Multiple calls are permitted and will stack – each invocation merely
        adjusts the base layer once.

        Exactly **one** of *position*, *zone_index* or *zone_name* must be
        provided.  The selected LEDs are modified in the base layer using the
        supplied hue/saturation/brightness offsets; other LEDs are unchanged.

        :param device: The target device (may be an object not yet added)
        :param position: LED index to correct (mutually exclusive with zones)
        :param zone_index: Numeric zone index to correct; ignores *position* and
                           *zone_name* if given.
        :param zone_name: Human-readable zone name; mutually exclusive with the
                          other selectors.
        :param hue_correction: Amount to adjust hue (-360.0 to 360.0)
        :param saturation_correction: Amount to adjust saturation (-100.0 to
                                      100.0)
        :param brightness_correction: Amount to adjust brightness (-100.0 to
                                      100.0)
        """

        selectors = [position is not None, zone_index is not None, zone_name is not None]
        if selectors.count(True) != 1:
            raise ValueError("must specify exactly one of position, zone_index or zone_name")

        record = (position, zone_index, zone_name,
                  hue_correction, saturation_correction, brightness_correction)

        # remember the correction in all cases; existing devices need
        # their layers re-written to pick up the change
        self.color_corrections.setdefault(device.id, []).append(record)
        if device in self.device_list:
            # rewrite base layer (and target) through set_layer so the new
            # record is applied immediately
            base = self.get_layer(device, self.layer_names[0])
            self.set_layer(device, self.layer_names[0], base)
            target = self.get_layer(device, self.layer_names[1])
            self.set_layer(device, self.layer_names[1], target)
                
    def get_colors(self, device) -> dict:
        return self.colors[device.id]
                
    def get_layer_names(self) -> list:
        return self.layer_names
    
    def get_layer(self, device, layer_name: str) -> list:
        return self.devices_layers[device.id][layer_name]
    
    def get_device(self) -> list:
        return self.device_list
    
    def add_device(self, device, color1, color2, color_2_percentage) -> None:
        # prepare layers before announcing the new device to avoid any
        # observer seeing an uncorrected frame
        layers = {layer: [None] * len(device.leds) for layer in self.layer_names}
        # base layer constructed from colour1
        base = set_base_color(device, color1)

        # corrections will be applied automatically by set_layer below once we
        # write the base back, so no need to preapply here
        layers[self.layer_names[0]] = base
        layers[self.layer_names[1]] = set_random_colors(device, color1, color2, color_2_percentage)

        # now that layers are ready we can safely add the device
        self.device_list.append(device)
        self.devices_layers[device.id] = layers
        self.colors[device.id] = [color1, color2, color_2_percentage]

        # rewrite both base and target via set_layer so corrections run on
        # any colour0 occurrences in either layer
        self.set_layer(device, self.layer_names[0], base)
        self.set_layer(device, self.layer_names[1], layers[self.layer_names[1]])
        
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

        layers = [self.get_layer(device, ln) for ln in self.layer_names[:4]]
        gradient_layer = [
            layers[0][led.id] if layers[3][led.id] == layers[2][led.id]
            else calculate_gradient(
                layers[0][led.id],
                layers[1][led.id],
                get_percentage_cached(layers[2][led.id], layers[3][led.id])
            )
            for zone in device.zones for led in zone.leds
        ]

        self.set_layer(device, self.layer_names[4], gradient_layer)

    def set_timings(self, device, min_steps: int, max_steps: int) -> None:
        layer_base = self.get_layer(device, self.layer_names[0])
        layer_target = self.get_layer(device, self.layer_names[1])
        layer_timing = self.get_layer(device, self.layer_names[2])
        layer_current = self.get_layer(device, self.layer_names[3])
        color1, color2, color_2_percentage = self.get_colors(device)

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
                        # copy target to base; set_layer below will reapply
                        # corrections for us
                        layer_base[led_id] = layer_target[led_id]
                        layer_target[led_id] = set_random_color(color1, color2, color_2_percentage)

        # no extra work needed here; set_layer will handle corrections

        if self.get_layer(device, self.layer_names[0]) != layer_base:
            self.set_layer(device, self.layer_names[0], layer_base)
        if self.get_layer(device, self.layer_names[1]) != layer_target:
            self.set_layer(device, self.layer_names[1], layer_target)
        if self.get_layer(device, self.layer_names[2]) != layer_timing:
            self.set_layer(device, self.layer_names[2], layer_timing)
        if self.get_layer(device, self.layer_names[3]) != layer_current:
            self.set_layer(device, self.layer_names[3], layer_current)

    def set_gradient(self, device, gradient_min_steps: int, gradient_max_steps: int) -> None:
        self.set_timings(device, gradient_min_steps, gradient_max_steps)
        self.gradient(device)
        
    def set_volume(self, device, volume) -> None:
        color1, color2, _ = self.get_colors(device)
        self.set_layer(device, self.layer_names[5],
                     set_volume(device, color1, color2, volume))
