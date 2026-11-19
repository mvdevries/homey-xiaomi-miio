Feature: The bedside lamp
  The Mi Bedside Lamp 2 is shown and controlled from Homey.

  Background:
    Given a bedside lamp that is on at 50% brightness
    And the device is added to Homey

  Scenario: Homey shows the state of the lamp
    Then Homey shows the device as on
    And Homey shows a level of 50%

  Scenario: The lamp is turned off from Homey
    When I turn the device off in Homey
    Then the device is switched off

  Scenario: The lamp is dimmed from Homey
    When I dim the device to 80% in Homey
    Then the device has a level of 80%

  Scenario: Dimming a lamp that is off turns it on
    When I turn the device off in Homey
    And I dim the device to 30% in Homey
    Then the device is switched on
    And the device has a level of 30%

  Scenario: Dimming to zero turns the lamp off
    When I dim the device to 0% in Homey
    Then the device is switched off

  Scenario: The warmest light is chosen
    When I choose the warmest light in Homey
    Then the device has a colour temperature of 1700 kelvin

  Scenario: A colour is chosen
    When I choose the colour red in Homey
    Then the device shines in the colour red

  Scenario: A change made at the lamp shows up in Homey
    When someone switches the device off at the device itself
    Then Homey shows the device as off
