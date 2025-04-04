# Testing Report for Access Control

## Overview

This document outlines the testing activities performed for the Access Control component. It details the environment, test cases, results, and any issues encountered during testing.

## Table of Contents

1. [Test Environment](#test-environment)
2. [Test Cases](#test-cases)
3. [Issues Encountered](#issues-encountered)
4. [Conclusion](#conclusion)
5. [Additional Notes](#additional-notes)
6. [Contributors](#contributors)

## Test Environment

- Testing Framework/Tools: **JUnit**, **SonarQube**
- Testing Environment: **Localhost**, **Cloud Deployment**
- Component version: **v0.5**

## Test Cases

| # | Description / Endpoint | Component | Status (Pass/Fail) |
| -------------- | -- | -- | -- |
| 1 | Component APIs - Integration & Unit Tests | Access Control | Pass |
| 2 | Authenticating JWT | MODAPTO Components | Pass |
| 3 | Retrieve userIds by User Role | Notification Center | Pass |
| 4 | Retrieve userIds by Pilot Code | Notification Center | Pass |
| 5 | Rate Limiting Test for REST calls | Access Control | Pass |
| 6 | Security Tests via SonarQube | Access Control | Pass |

## Issues Encountered

***NONE***

## Conclusion

- Overall Component Status: **Stable**

- Recommended Actions:

  - Add postman collection for tests or create a Postman pipeline to implement a sequence of API calls for testing

## Additional Notes

***NONE***

## Contributors

- Alkis Aznavouridis (<a.aznavouridis@atc.gr>)
