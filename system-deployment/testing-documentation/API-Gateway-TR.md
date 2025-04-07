# Testing Report for API Gateway

## Overview

This document outlines the testing activities performed for the API Gateway component. It details the environment, test cases, results, and any issues encountered during testing

***Note***: API Gateway is a Reverse Proxy tool utilizing Traefik for mapping services / containers, enabling load balancing and exposing these services to specific URLs / Domains.

## Table of Contents

1. [Test Environment](#test-environment)
2. [Test Cases](#test-cases)
3. [Issues Encountered](#issues-encountered)
4. [Conclusion](#conclusion)
5. [Additional Notes](#additional-notes)
6. [Contributors](#contributors)

## Test Environment

- Testing Framework/Tools: **Traefik Environment**
- Testing Environment: **Cloud Deployment**
- Component version: **v0.5**

## Test Cases

| # | Description / Endpoint | Component | Status (Pass/Fail) |
| -------------- | -- | -- | -- |
| 1 | Expose MODAPTO Components via HTTPS | MODAPTO Components | Pass |
| 2 | Expose MODAPTO Components via TCP | API Gateway | Pass |
| 3 | Generate TLS Certificate for new Component | API Gateway  | Pass |
| 4 | Redirecting HTTP to HTTPS | API Gateway | Pass |
| 5 | Restricting Ingress to Message Bus | API Gateway | Not Tested |
| 6 | Traefik UI presents all services | API Gateway | Pass |

## Issues Encountered

| # | Description | Severity (Low/Medium/High) | Status (Open/Resolved) |
| -------------- | -- | -- | -- |
| 1 | Message Bus enables both Ingress / Egress from external source | Low | Open |

## Conclusion

- Overall Component Status: **Stable**

- Recommended Actions:

  - Restrict Ingress of Message Bus via applying specific TCP rules.

## Additional Notes

***NONE***

## Contributors

- Alkis Aznavouridis (<a.aznavouridis@atc.gr>)
