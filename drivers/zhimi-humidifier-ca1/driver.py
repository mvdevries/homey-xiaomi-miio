from app.endpoints.pairing_driver import MiioDriver


class HumidifierDriver(MiioDriver):
    models = ("zhimi.humidifier.ca1", "zhimi.humidifier.cb1")


homey_export = HumidifierDriver
