Feature: Logging in with a Xiaomi account
  The user scans a QR code with the Mi Home app, and the app reads the devices and their tokens from the account.

  Background:
    Given a Xiaomi account with a bedside lamp named "Bedside lamp" at 192.0.2.10
    And the same Xiaomi account has a smart speaker named "Kitchen speaker"

  Scenario: Starting the login shows a QR code
    When I start logging in with the Xiaomi account
    Then I get a QR code to scan
    And the login is waiting for the scan

  Scenario: Scanning the QR code lists the devices that this driver supports
    Given I started logging in with the Xiaomi account
    When the user scans the QR code in the Mi Home app
    Then the login is complete
    And I see only the device "Bedside lamp" at 192.0.2.10 with its token

  Scenario: Asking for devices before the scan is rejected
    Given I started logging in with the Xiaomi account
    When I ask for the devices of the account
    Then the request is rejected with "not_signed_in"

  Scenario: A login without a service token fails
    Given the Xiaomi account does not hand out a service token
    And I started logging in with the Xiaomi account
    When the user scans the QR code in the Mi Home app
    Then the login has failed

  Scenario: A cloud that is down cannot start a login
    Given the Xiaomi cloud is down
    When I start logging in with the Xiaomi account
    Then the request is rejected with "login_unavailable"
