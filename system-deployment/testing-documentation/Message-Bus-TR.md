# Testing Report for Message Bus

## Overview

This document outlines the testing activities performed for the Message Bus component. It details the environment, test cases, results, and any issues encountered during testing

***Note***: Message Bus is a set of configuration for Kafka Cluster and its associated tools. The tests conducted include these integrations and their results.

## Table of Contents

1. [Test Environment](#test-environment)
2. [Test Cases](#test-cases)
3. [Issues Encountered](#issues-encountered)
4. [Conclusion](#conclusion)
5. [Additional Notes](#additional-notes)
6. [Contributors](#contributors)

## Test Environment

- Testing Framework/Tools: **Kafka Environment**
- Testing Environment: **Localhost**, **Cloud Deployment**
- Component version: **v0.5**

## Test Cases

| # | Description / Endpoint | Component | Status (Pass/Fail) |
| -------------- | -- | -- | -- |
| 1 | Initialization in Docker - Service 'Healthy' | Message Bus | Pass |
| 2 | Visualization of Cluster info | Kafka UI | Pass |
| 3 | Register new Topics | Message Bus | Pass |
| 4 | Store messages after re-initialization | Message Bus | Pass |
| 5 | Register Schemas for Messages | Schema Registry | Pass |
| 6 | Expose REST interface for Kafka Cluster | Kafka REST Proxy | Pass |
| 7 | Handles messages from MODAPTO Components * | MODAPTO Components ** | Pass |
| 8 | Pass messages to MODAPTO Components * | MODAPTO Components **| Pass |

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

****Note**: Not all MODAPTO Components publish / subscribe to Kafka Cluster. A brief list of publishers / consumers is presented:

### Publishers

- Digital Twin Management

### Consumers

- Notification Center
- Evaluation and Decision Support
- Production Knowledge Base

## Issues Encountered

***NONE***

## Conclusion

- Overall Component Status: **Stable**

- Recommended Actions:

  - Configure specific message Schemas for MODAPTO use-case
  - Setup 3 Broker/Controller environment for high scalability and data integrity

## Additional Notes

***NONE***

## Contributors

- Alkis Aznavouridis (<a.aznavouridis@atc.gr>)
