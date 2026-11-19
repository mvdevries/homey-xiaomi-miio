from app.endpoints.pairing_driver import MiioDriver


class HumidifierDriver(MiioDriver):
    pass


homey_export = HumidifierDriver
