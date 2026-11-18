from tests.support import load_module

app_module = load_module("app")


async def test_on_init_logs_the_start():
    logged = []

    class Recorder(app_module.App):
        def log(self, *args):
            logged.append(args)

    await Recorder().on_init()

    assert logged == [("Xiaomi MiIO started",)]
