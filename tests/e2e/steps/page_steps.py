import pytest
from app.domain.discovery import DiscoveredDevice
from playwright.sync_api import expect
from pytest_bdd import given, parsers, then, when

from tests.support.fake_miio_devices import DEVICE_ADDRESS, DEVICE_TOKEN_HEX
from tests.support.loop_harness import wait_until

DRIVER_IDS = {
    "bedside lamp": "yeelink-light-bslamp2",
    "standing fan": "zhimi-fan-za4",
    "humidifier": "zhimi-humidifier-ca1",
}


@pytest.fixture
def open_pairing_page(pairing_page):
    return pairing_page


@given("a device answers at the address")
def a_device_answers_at_the_address(backend):
    backend.lamp.silent = False


@given("no device answers at the address")
def no_device_answers_at_the_address(backend):
    backend.lamp.silent = True


@given(parsers.parse("a device is found on the network at {address}"))
@when(parsers.parse("a device is found on the network at {address}"))
def a_device_is_found_on_the_network(backend, address):
    backend.discovered_devices.append(DiscoveredDevice(address, 0x1234))


@given(parsers.parse('a device named "{name}" is found on the network at {address}'))
def a_named_device_is_found_on_the_network(backend, name, address):
    backend.discovered_devices.append(DiscoveredDevice(address, 0x1234, name))


@given("no device is found on the network")
def no_device_is_found_on_the_network(backend):
    backend.discovered_devices.clear()


@when(parsers.parse("I choose the found device at {address}"))
def i_choose_the_found_device(page, address):
    page.locator(".device-row", has_text=address).click()


@when("I continue")
def i_continue(page):
    page.locator("#continue").click(force=True)


@when("I search again")
def i_search_again(page):
    page.locator("#scan").click()


@when(parsers.parse("I open the start page of the {device}"))
def i_open_the_start_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device], view="start")


@when(parsers.parse("I open the search page of the {device}"))
def i_open_the_search_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device], view="discover")


@when("I choose to search for devices")
def i_choose_to_search(page):
    page.locator("#search").click()


@when("I choose to enter the details myself")
def i_choose_to_enter_the_details(page):
    page.locator("#manual").click()


@when(parsers.parse("I open the pairing page of the {device}"))
def i_open_the_pairing_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device])


@when(parsers.parse("I open the Dutch pairing page of the {device}"))
def i_open_the_dutch_pairing_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device], "nl")


@when(parsers.parse('I enter the name "{name}"'))
def i_enter_the_name(page, name):
    page.locator("#name").fill(name)


@when("I enter the address of the device")
def i_enter_the_address(page):
    page.locator("#address").fill(DEVICE_ADDRESS)


@when(parsers.parse('I enter the token "{token}"'))
def i_enter_a_token(page, token):
    page.locator("#token").fill(token)


@when("I enter the address and token of the device")
def i_enter_the_address_and_token(page):
    page.locator("#address").fill(DEVICE_ADDRESS)
    page.locator("#token").fill(DEVICE_TOKEN_HEX)


@when("I add the device")
def i_add_the_device(page):
    page.locator("#add").click()


@then("I see the fields for the name, address, token and polling interval")
def i_see_the_fields(page):
    for field in ("#name", "#address", "#token", "#polling"):
        expect(page.locator(field)).to_be_visible()


@then(parsers.parse('the page title is "{title}"'))
def the_page_title_is(page, title):
    page.wait_for_function("window.pairTitle !== undefined")
    assert page.evaluate("window.pairTitle") == title


@then(parsers.parse('I see the button "{text}"'))
def i_see_the_button(page, text):
    expect(page.get_by_role("button", name=text)).to_be_visible()


@then(parsers.parse('I see the message "{text}"'))
def i_see_the_message(page, text):
    expect(page.locator("#toast")).to_have_text(text)


@then(parsers.parse('the device "{name}" is created in Homey'))
def the_device_is_created(backend, name):
    wait_until(
        lambda: any(device["name"] == name for device in backend.created_devices)
    )
    created = backend.created_devices[0]
    assert created["settings"]["address"] == DEVICE_ADDRESS
    assert created["settings"]["token"] == DEVICE_TOKEN_HEX


@then("no device is created in Homey")
def no_device_is_created(backend):
    assert backend.created_devices == []


@then("the pairing is finished")
def the_pairing_is_finished(page):
    page.wait_for_function("window.pairDone === true")


@then(parsers.parse("I see the found device at {address}"))
def i_see_the_found_device(page, address):
    expect(page.locator(".device-row", has_text=address)).to_be_visible()


@then(parsers.parse('I see the text "{text}"'))
def i_see_the_text(page, text):
    expect(page.locator("#found")).to_contain_text(text)


@then(parsers.parse("the address field contains {address}"))
def the_address_field_contains(page, address):
    expect(page.locator("#address")).to_have_value(address)


@then("I see the search page")
def i_see_the_search_page(page):
    expect(page.locator("#found")).to_be_visible()


@then(parsers.parse('I see the found device named "{name}" at {address}'))
def i_see_the_named_found_device(page, name, address):
    row = page.locator(".device-row", has_text=name)
    expect(row).to_contain_text(address)


@then(parsers.parse('I see the warning "{text}"'))
def i_see_the_warning(page, text):
    expect(page.get_by_role("note")).to_contain_text(text)


@then("I still see the search page")
def i_still_see_the_search_page(page):
    expect(page.locator("#found")).to_be_visible()
    expect(page.locator("#name")).to_have_count(0)


@then(parsers.parse('the name field contains "{name}"'))
def the_name_field_contains(page, name):
    expect(page.locator("#name")).to_have_value(name)


@then(parsers.parse('I see the identifier "{identifier}" in the row of {address}'))
def i_see_the_identifier(page, identifier, address):
    row = page.locator(".device-row", has_text=address)
    expect(row.locator(".device-identifier")).to_have_text(identifier)


@given(
    parsers.parse('my Xiaomi account has a bedside lamp named "{name}" at {address}')
)
def my_account_has_a_bedside_lamp(backend, name, address):
    backend.cloud.add_device(
        "de",
        did="1001",
        name=name,
        model="yeelink.light.bslamp2",
        token=DEVICE_TOKEN_HEX,
        localip=address,
    )


@given(parsers.parse('my Xiaomi account also has a smart speaker named "{name}"'))
def my_account_has_a_speaker(backend, name):
    backend.cloud.add_device(
        "de",
        did="1002",
        name=name,
        model="xiaomi.wifispeaker.l09g",
        token="ff" * 16,
        localip="192.0.2.30",
    )


@given("my Xiaomi account does not hand out a service token")
def my_account_hands_out_no_token(backend):
    backend.cloud.refuse_service_token = True


@when("I choose to log in with my Xiaomi account")
def i_choose_to_log_in(page):
    page.locator("#account").click()


@when(parsers.parse("I open the account page of the {device}"))
def i_open_the_account_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device], view="account")


@when(parsers.parse("I open the Dutch account page of the {device}"))
def i_open_the_dutch_account_page(open_pairing_page, device):
    open_pairing_page(DRIVER_IDS[device], "nl", view="account")


@when("I scan the QR code with the Mi Home app")
def i_scan_the_qr_code(page, backend):
    expect(page.locator("#qr-image")).to_be_visible()
    backend.cloud.scanned = True


@when(parsers.parse('I choose the account device "{name}"'))
def i_choose_the_account_device(page, name):
    page.locator(".device-row", has_text=name).click()


@then("I see the QR code")
def i_see_the_qr_code(page):
    expect(page.locator("#qr-image")).to_be_visible()
    assert page.locator("#qr-image").get_attribute("src").startswith("data:image/")


@then(parsers.parse('I see the text "{text}" in the status'))
def i_see_the_text_in_the_status(page, text):
    expect(page.locator("#status")).to_have_text(text)


@then(parsers.parse('I see the text "{text}" in the account list'))
def i_see_the_text_in_the_account_list(page, text):
    expect(page.locator("#found")).to_contain_text(text)


@then(parsers.parse('I see the account device "{name}" at {address}'))
def i_see_the_account_device(page, name, address):
    row = page.locator(".device-row", has_text=name)
    expect(row).to_contain_text(address)


@then(parsers.parse('I do not see the account device "{name}"'))
def i_do_not_see_the_account_device(page, name):
    expect(page.locator(".device-row", has_text=name)).to_have_count(0)


@then("the token field is filled in")
def the_token_field_is_filled_in(page):
    expect(page.locator("#token")).to_have_value(DEVICE_TOKEN_HEX)
