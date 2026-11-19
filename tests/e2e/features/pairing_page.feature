Feature: The pairing page
  The user adds a device by entering its name, address and token.

  Scenario Outline: The page asks for the details of the device
    When I open the pairing page of the <device>
    Then I see the fields for the name, address, token and polling interval
    And the page title is "Add a Xiaomi device"

    Examples:
      | device       |
      | bedside lamp |
      | standing fan |
      | humidifier   |

  Scenario: The page is shown in Dutch
    When I open the Dutch pairing page of the bedside lamp
    Then the page title is "Xiaomi-apparaat toevoegen"
    And I see the button "Apparaat toevoegen"

  Scenario: A device that answers is added
    Given a device answers at the address
    When I open the pairing page of the bedside lamp
    And I enter the name "Reading light"
    And I enter the address and token of the device
    And I add the device
    Then I see the message "Device added"
    And the device "Reading light" is created in Homey
    And the pairing is finished

  Scenario: A device that does not answer is rejected
    Given no device answers at the address
    When I open the pairing page of the bedside lamp
    And I enter the name "Reading light"
    And I enter the address and token of the device
    And I add the device
    Then I see the message "Cannot reach the device. Check the IP address and token."
    And no device is created in Homey

  Scenario: A token that is not hexadecimal is rejected
    When I open the pairing page of the bedside lamp
    And I enter the name "Reading light"
    And I enter the address of the device
    And I enter the token "not-a-token"
    And I add the device
    Then I see the message "The token must be 32 hexadecimal characters."
    And no device is created in Homey

  Scenario: A device needs a name
    When I open the pairing page of the bedside lamp
    And I enter the address and token of the device
    And I add the device
    Then I see the message "Enter a name and an IP address."

  Scenario: The rejection is shown in Dutch
    Given no device answers at the address
    When I open the Dutch pairing page of the bedside lamp
    And I enter the name "Leeslamp"
    And I enter the address and token of the device
    And I add the device
    Then I see the message "Het apparaat is niet bereikbaar. Controleer het IP-adres en de token."

  Scenario: The start page offers searching or entering the details
    When I open the start page of the bedside lamp
    Then I see the button "Search for devices on my network"
    And I see the button "Enter the details myself"

  Scenario: The start page warns that the IP address must stay the same
    When I open the start page of the bedside lamp
    Then I see the warning "Give your device a fixed IP address in your router, so Homey keeps finding it."

  Scenario: Choosing to search opens the search page
    When I open the start page of the bedside lamp
    And I choose to search for devices
    Then I see the search page

  Scenario: Choosing to enter the details opens the form
    When I open the start page of the bedside lamp
    And I choose to enter the details myself
    Then I see the fields for the name, address, token and polling interval

  Scenario: A device found on the network fills in the address
    Given a device is found on the network at 192.0.2.10
    When I open the search page of the bedside lamp
    Then I see the found device at 192.0.2.10
    When I choose the found device at 192.0.2.10
    And I continue
    Then the address field contains 192.0.2.10

  Scenario: The name of a found device is filled in as the name
    Given a device named "zhimi-fan-za4_mibt0FE4" is found on the network at 192.0.2.10
    When I open the search page of the standing fan
    And I choose the found device at 192.0.2.10
    And I continue
    Then the name field contains "Mi Smart Standing Fan"

  Scenario: Choosing a found device does not continue by itself
    Given a device is found on the network at 192.0.2.10
    When I open the search page of the bedside lamp
    And I choose the found device at 192.0.2.10
    Then I still see the search page

  Scenario: Continuing needs a chosen device
    Given a device is found on the network at 192.0.2.10
    When I open the search page of the bedside lamp
    And I continue
    Then I still see the search page

  Scenario: A found device is shown with the name it has on the network
    Given a device named "zhimi-fan-za4_mibt0FE4" is found on the network at 192.0.2.10
    When I open the search page of the standing fan
    Then I see the found device named "Mi Smart Standing Fan" at 192.0.2.10
    And I see the identifier "00001234" in the row of 192.0.2.10

  Scenario: A found device with an unknown model keeps its network name
    Given a device named "acme-gadget-x1_mibt1" is found on the network at 192.0.2.11
    When I open the search page of the standing fan
    Then I see the found device named "acme-gadget-x1_mibt1" at 192.0.2.11

  Scenario: A network without devices tells the user to enter the address
    Given no device is found on the network
    When I open the search page of the bedside lamp
    Then I see the text "No devices found. Enter the IP address yourself."

  Scenario: Searching again shows a device that appeared
    Given no device is found on the network
    When I open the search page of the bedside lamp
    And a device is found on the network at 192.0.2.10
    And I search again
    Then I see the found device at 192.0.2.10
