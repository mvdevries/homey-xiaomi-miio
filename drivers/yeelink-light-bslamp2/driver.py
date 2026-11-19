from app.endpoints.pairing_driver import MiioDriver


class BedsideLampDriver(MiioDriver):
    models = ("yeelink.light.bslamp2",)


homey_export = BedsideLampDriver
