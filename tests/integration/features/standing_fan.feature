Feature: The standing fan
  The Mi Smart Standing Fan is shown and controlled from Homey.

  Background:
    Given a standing fan that is switched off
    And the device is added to Homey

  Scenario: Homey shows the state of the fan
    Then Homey shows the device as off
    And Homey shows a level of 40%
    And Homey shows the oscillation as off
    And Homey shows an oscillation angle of 90 degrees

  Scenario: The fan is turned on from Homey
    When I turn the device on in Homey
    Then the device is switched on

  Scenario: The speed is set from Homey
    When I turn the device on in Homey
    And I dim the device to 70% in Homey
    Then the device has a level of 70%

  Scenario: The oscillation is turned on from Homey
    When I turn the oscillation on in Homey
    Then the device oscillates over 90 degrees

  Scenario: An oscillation angle is chosen from Homey
    When I set the oscillation angle to 120 degrees in Homey
    Then the device is set to an angle of 120 degrees
    And Homey shows an oscillation angle of 120 degrees

  Scenario: An angle between two steps is rounded to the nearest one
    When I set the oscillation angle to 110 degrees in Homey
    Then the device is set to an angle of 120 degrees

  Scenario: The LED display is turned off from Homey
    When I turn the LED display off in Homey
    Then the device has its LED display switched off

  Scenario: The buzzer is turned on from Homey
    When I turn the buzzer on in Homey
    Then the device has its buzzer switched on

  Scenario: The child lock is turned on from Homey
    When I turn the child lock on in Homey
    Then the device has its child lock switched on

  Scenario: A change made at the fan shows up in Homey
    When someone switches the device on at the device itself
    Then Homey shows the device as on
