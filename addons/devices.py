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
        
    def setGradient(self, device, gradient_min_steps: int, gradient_max_steps: int) -> None:
        color1, color2, color_2_percentage = self.getColors(device)
        layers = [self.getLayer(device, ln) for ln in self.layer_names[:4]]
        
        output = set_timings(device, layers, gradient_min_steps, gradient_max_steps, color1, color2, color_2_percentage)
        for layer_name, layer_data in zip(self.layer_names[:4], output):
            self.setLayer(device, layer_name, layer_data)
        
        final_layer = gradient(device, layers)
        self.setLayer(device, self.layer_names[4], final_layer)
        
    def setVolume(self, device) -> None:
        color1, color2, _ = self.getColors(device)
        self.setLayer(device, self.layer_names[5],
                     set_volume(device, color1, color2))
