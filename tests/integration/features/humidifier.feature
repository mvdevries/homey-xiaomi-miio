Feature: The humidifier
  The Mi Smart Humidifier is shown and controlled from Homey.

  Background:
    Given a humidifier that is switched off
    And the device is added to Homey

  Scenario: Homey shows the state of the humidifier
    Then Homey shows the device as off
    And Homey shows a humidity of 41%
    And Homey shows a temperature of 21.5 degrees
    And Homey shows the mode "auto"
    And Homey shows a target humidity of 50%

  Scenario: The humidifier is turned on from Homey
    When I turn the device on in Homey
    Then the device is switched on

  Scenario: Choosing a mode on a humidifier that is off turns it on
    When I choose the mode "high" in Homey
    Then the device is switched on
    And the device runs in the mode "high"

  Scenario: The target humidity is set from Homey
    When I set the target humidity to 60% in Homey
    Then the device aims for a humidity of 60%

  Scenario: The dry mode is turned on from Homey
    When I turn the dry mode on in Homey
    Then the device has its dry mode switched on

  Scenario: The child lock is turned on from Homey
    When I turn the child lock on in Homey
    Then the device has its child lock switched on

  Scenario: The LED display is turned off from Homey
    When I turn the LED display off in Homey
    Then the device has its LED display switched off

  Scenario: A change made at the humidifier shows up in Homey
    When someone switches the device on at the device itself
    Then Homey shows the device as on
