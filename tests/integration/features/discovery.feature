Feature: Discovering devices
  Devices on the network answer a broadcast, so the user does not have to type an address.

  Scenario: A device on the network is found
    Given a bedside lamp that is on at 50% brightness
    When I search for devices on the network
    Then I find 1 device
    And the found device has an address, an identifier and the name it has on the network

  Scenario: An empty network finds nothing
    When I search for devices on an empty network
    Then I find 0 devices
