Feature: The natural wind of the standing fan
  A fan that blows natural wind keeps blowing natural wind when the speed is changed.

  Scenario: Homey shows the speed of the natural wind
    Given a standing fan that blows natural wind at 55% speed
    When the device is added to Homey
    Then Homey shows a level of 55%

  Scenario: The speed of the natural wind is changed from Homey
    Given a standing fan that blows natural wind at 55% speed
    And the device is added to Homey
    When I dim the device to 70% in Homey
    Then the device blows natural wind at 70% speed
