# Rule: tests

- Every change comes with tests: unit tests for logic, integration tests for the devices against a fake miIO
  device, end-to-end tests for the pairing page. Coverage must stay at or above 90%.
- Unit tests mirror the layers (`tests/unit/domain`, `application`, `infrastructure`, `endpoints`) and the
  driver folders (`tests/unit/drivers`), one test file per source file and one `Test<Unit>` class per unit. A
  test is named `test_given_<state>_when_<action>_then_<result>` and has its arrange, act and assert parts
  separated by blank lines.
- Integration and end-to-end tests are Gherkin scenarios: `.feature` files in `tests/integration/features` and
  `tests/e2e/features`, with the steps in `tests/integration/steps` and `tests/e2e/steps`. Write scenarios in
  plain sentences a user would recognise, and reuse existing steps before adding new ones.
- Integration tests run the real code (the Homey device classes, the services and the UDP transport) against a
  fake miIO device on the loopback address. End-to-end tests drive the pairing page in a real browser, with the
  real pairing code behind a small local server.
- Test devices are generic and come from `tests/support`. Never use real devices, names, addresses or tokens in
  tests, fixtures or snapshots.
