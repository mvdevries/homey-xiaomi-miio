from app.endpoints.pairing_driver import MiioDriver


class StandingFanDriver(MiioDriver):
    models = ("zhimi.fan.za4",)


homey_export = StandingFanDriver
