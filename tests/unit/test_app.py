from tests.support import load_module

app_module = load_module("app")


class TestApp:
    async def test_given_an_app_when_initialised_then_the_start_is_logged(self):
        logged = []

        class Recorder(app_module.App):
            def log(self, *args):
                logged.append(args)

        await Recorder().on_init()

        assert logged == [("Xiaomi MiIO started",)]
