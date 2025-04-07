# Testing Report for Digital Twin

## Overview

This document outlines the testing activities performed for the Digital Twin. It details the environment, test cases, results, and any issues encountered during testing.

## Table of Contents

1. [Test Environment](#test-environment)
2. [Test Cases](#test-cases)
3. [Issues Encountered](#issues-encountered)
4. [Conclusion](#conclusion)
5. [Additional Notes](#additional-notes)

## Test Environment

- Testing Framework/Tools: JUnit, OWASP, SonarQube, manual tests
- Testing Environment: multiple (local for unit tests, manual tests have been executed locally and on cloud deployment)
- Component version: 0.5.0-SNAPSHOT (commit [345db36](https://github.com/Modapto/digital-twin/commit/345db368df3573d13e8d2b292bbc63a64cf35880))

## Test Cases

| # | Description / Endpoint | Component | Status (Pass/Fail) |
| -------------- | -- | -- | -- |
| 1 | Component APIs - Integration & Unit Tests | Digital Twin | Pass |
| 2 | Event forwarding to Digital Twin Management | Digital Twin | Pass |
| 3 | Handle SMT Simulation | Digital Twin | Pass |
| 4 | Parse FMUs and create operation to execute FMU logic | Digital Twin | Pass |
| 5 | Invoke Embedded Smart Service | Digital Twin | Pass |
| 6 | Invoke Internal Smart Service | Digital Twin | Pass |
| 7 | Invoke External Smart Service | Digital Twin | Pass |

*Note: #1 has to do with the component itself, that is fully tested, e.g. with Postman as well to Unit & Integration Tests

## Issues Encountered

| # | Description | Severity (Low/Medium/High) | Status (Open/Resolved) |
| -------------- | -- | -- | -- |

## Conclusion

- Overall Component Status: Stable

- Recommended Actions:

## Additional Notes

MODAPTO Digital Twin is based on FA³ST Service which itself has been thoroughly tested.
Therefore, the only additional tests that have been to execute are related to FMU handling and execution of Smart Services.
