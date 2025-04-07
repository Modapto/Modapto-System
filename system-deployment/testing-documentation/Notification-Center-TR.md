# Testing Report for Notification Center

## Overview

This document outlines the testing activities performed for the Notification Center component. It details the environment, test cases, results, and any issues encountered during testing.

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
| 1 | Component APIs - Integration & Unit Tests | Notification Center | Pass |
| 2 | Consume events and generate Notifications* | Message Bus | Pass |
| 3 | Connect with Elasticsearch and retrieve data | Production Knowledge Base | Pass |
| 4 | Rate Limiting Test for REST calls | Notification Center | Pass |
| 5 | Security Tests via SonarQube | Notification Center | Pass |

***Note**: The topics that were tested are the ones configured in Message Bus and are the following:

- self-awareness-diagnosis
- self-awareness-detection
- predictive-maintenance
- process-drift
- production-schedule-update
- delivery-delay
- production-schema-registration
- smart-service-event
- modapto-module-creation
- modapto-module-deletion
- modapto-module-update
- smart-service-invoke
- smart-service-finish
- modapto-mqtt-topics

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
