class Devices:
    def __init__(self,) -> None:
        self.devices = []
        self.devices_layers = {}
        self.layer_names = [
            "layer_1_base",  # * ID 0
            "layer_1_target",  # * ID 1
            "layer_1_timing",  # * ID 2
            "layer_1_current",  # * ID 3
            "layer_1_final",  # * ID 4
            "layer_2_volume",  # * ID 5
            ]
    
    def addDevice(self, device) -> None:
        self.devices.append(device)
        self.devices_layers[device.id] = {}
        for j in self.layer_names:
            self.devices_layers[device.id][j] = []
            for led in device.leds:
                self.devices_layers[device.id][j].append(None)
                
    def setLayer(self, device, layer_name: str, layer: list) -> None:
        self.devices_layers[device.id][layer_name] = layer
                
    def get_layer_names(self) -> list:
        return self.layer_names
    
    def getLayer(self, device, layer_name: str) -> list:
        return self.devices_layers[device.id][layer_name]
    
    def getDevices(self) -> list:
        return self.devices