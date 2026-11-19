Feature: The connection with a device
  Homey shows a device as unavailable as long as it does not answer.

  Scenario: A device that does not answer is unavailable
    Given a bedside lamp that is on at 50% brightness
    And the device does not answer
    When the device is added to Homey
    Then Homey marks the device as unavailable

  Scenario: A device that stops answering becomes unavailable
    Given a bedside lamp that is on at 50% brightness
    And the device is added to Homey
    When the device does not answer anymore
    Then Homey marks the device as unavailable

  Scenario: A device that answers again becomes available
    Given a bedside lamp that is on at 50% brightness
    And the device does not answer
    And the device is added to Homey
    When the device answers again
    Then Homey marks the device as available
    And Homey shows the device as on
