# Testing Report for Evaluation and Decision Support

## Overview

This document outlines the testing activities performed for the Evaluation and Decision Support component. It details the environment, test cases, results, and any issues encountered during testing.

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

| # | Description / Endpoint | Component | Status (Pass/Fail/Not Tested) |
| -------------- | -- | -- | -- |
| 1 | Component APIs - Integration & Unit Tests | Evaluation and Decision Support | Pass |
| 2 | Consume events for Smart Services operations* | Message Bus | Pass |
| 3 | Connect with Elasticsearch and retrieve data | Production Knowledge Base | Pass |
| 4 | Rate Limiting Test for REST calls | Evaluation and Decision Support | Pass |
| 5 | Security Tests via SonarQube | Evaluation and Decision Support | Pass |
| 6 | Retrieve DTs information | Digital Twin Management | Not Tested |
| 7 | Submit AAS specifications | Digital Twin Management | Not Tested |

***Note**: The topics that were tested are the ones configured in Message Bus and were specifically used by EDS:

- self-awareness-diagnosis
- self-awareness-detection
- predictive-maintenance
- smart-service-event
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
