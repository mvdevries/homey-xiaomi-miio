Feature: Pairing a device
  A device is only added when its details are valid and the device answers.

  Background:
    Given a bedside lamp that is on at 50% brightness

  Scenario: A device that answers is paired
    When I pair the device named "Reading light" with its address and token
    Then the pairing is accepted
    And the paired device is called "Reading light"

  Scenario: A device that does not answer is rejected
    Given the device does not answer
    When I pair the device named "Reading light" with its address and token
    Then the pairing is rejected with "device_unreachable"

  Scenario: A device with another token is rejected
    When I pair the device with the token "ffeeddccbbaa99887766554433221100"
    Then the pairing is rejected with "device_unreachable"

  Scenario: A token that is not hexadecimal is rejected
    When I pair the device with the token "not-a-token"
    Then the pairing is rejected with "token_invalid"

  Scenario: A device needs a name
    When I pair a device without a name
    Then the pairing is rejected with "name_and_address_required"

  Scenario: The polling interval is never shorter than five seconds
    When I pair the device with a polling interval of 1 seconds
    Then the pairing is accepted
    And the paired device is polled every 5 seconds
