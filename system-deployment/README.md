# MODAPTO System Deployment

## Overview

MODAPTO System can be deployed via Docker and Docker Compose into a specified Host Machine.

**The deployment consists of the following components:**

- Access Control (User Manager + Identity Manager)
- User Interface
- Evaluation and Decision Support
- API Gateway
- Digital Twin (DT) Management
- Service Catalogue
- Orchestrator
- Notification Center
- Message Bus (Kafka Broker + Kafka Connect + MQTT Broker + Kafka Rest Proxy + Kafka UI + Kafka Schema Registry)
- Production Knowledge Base (ELK Stack)

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Deployment](#deployment)
4. [Testing Documentation](#testing-documentation)
5. [Contributors](#contributors)

## Installation

As MODAPTO's System Deployment relies on Docker and Docker Compose make sure you have installed and configured properly those tools according to the Host's OS.

- **Setup Docker**: <https://www.docker.com/get-started/>
- **Setup Docker Compose**: <https://docs.docker.com/compose/install/>

## Configuration

MODAPTO is configured and wrapped in such way to minimize deployment configuration. However, **some environmental variables and few configuration shall be implemented**. Morever:

- **In .env file**: Gateway URLs (**specified in the first section**) and credentials variables (**specified in the second section**) must be altered. The former shall be configured according to the assigned domain. We highly suggest the subdomains to be left as is. The latter can be specified according to user's preferences.

  - Important: **KEYCLOAK_CLIENT_SECRET** must be configured after the initial setup. See details and images below.

- **In api-gateway files:**: In directory ***/api-gateway/config/*** there are two files available regarding configuration of Traefik Reverse Proxy.

  - In file ***traefik.toml*** users shall insert an email address in the specified field.
  - In file ***traefik_dynamic.toml*** users shall configure the URL of Traefik UI and set up the available URLs that will be successfully routed through CORS. Can also be set to enable requests from all URLs (*).

It is important to initially set the username/password for the Traefik UI. To do so, you need to inject into ***traefik_dynamic.toml*** a hashed password. For generating the combination of username:password run the following command in the terminal:

```sh
# Generate a hashed password using htpasswd
htpasswd -nb [user] [password]
```

Copy the generated hashed value and add it under the ***[hostPath]*** field in the ***traefik_dynamic.toml***.

**NOTE:** If user's change some further environment variables in ***.env*** file, then other changes might be needed to the rest configuration files.

## Deployment

For the Deployment the process is being implemented into three steps:

1. Setting up the configuration for MODAPTO
2. Configure the Keycloak Client Secret and Update the .env file accordingly
3. Deploy all other components

### Step 1: Configure MODAPTO

To start the configuration of MODAPTO simply run (Linux environement):

 ```sh
chmod +x setup.sh
./setup.sh
 ```

For Windows just execute the file ***setup.bat***.

This step ensures that Docker and Docker Compose are available, change permissions to some files in the Host machine, setup ELK stack and deploy API-Gateway and Identity Manager in the system.

### Step 2: Configure Keycloak Client Secret

All MODAPTO components are authenticated and authrorized via Identity Manager. Hence, upon the initialization of the service, a new Keycloak Client Secret must be configured. Implement the following:

1. Access Keycloak URL specified in .env: **https://{KEYCLOAK_GATEWAY_URL}**
2. Change to ***modapto-system*** realm
3. Select client (*default:modapto*)
4. Navigate to credentials
5. Regenerate a new Token
6. Copy its value and add it to ***.env*** file in the specified variable

![Generate Token](https://github.com/Modapto/modapto-deployment/blob/main/MODAPTO%20System%20Deployment/resources/Generate_Token.png)

Additionally, its highly suggested to add the Super Admin of the System via the following process:

1. Access Keycloak URL specified in .env: **https://{KEYCLOAK_GATEWAY_URL}**
2. Change to ***modapto-system*** realm
3. Select "Realm Settings"
4. On the Top Right corner select "Actions"
5. Select "Partial Import"
6. Provide either the raw JSON context of "init-user-import.json*** file or the file itself.
7. Selecte the User
8. Press "Import"
9. Change Super-Admins password in Users Tab, select the User and navigate to Credentials to setup a new password

![Create Super Admin](https://github.com/Modapto/modapto-deployment/blob/main/MODAPTO%20System%20Deployment/resources//Import_User.png)

### Step 3: Deploy MODAPTO System

To deploy all other MODAPTO components just execute the following:

```sh
docker compose up -d
```

To stop all MODAPTO containers execute:

```sh
docker compose down
```

To stop API Gateway:

```sh
docker compose down traefik
```

***NOTE***: ELK stack operates under a free 30-day trial usage. After that period, users have to switch to the Basic License from Kibana UI. MODAPTO will still operate with the same functionalities with no additional effort or without any malfunction. To change the License of ELK, go to Kibana UI and search for "LICENSE" in the search field. Navigate to the single result and select to switch to default "Basic License". This step can be achieved also upon initialization of MODAPTO System.

## Testing Documentation

MODAPTO provides a comprehensive testing documentation process, including detailed test cases and reports. You can find the testing documentation in the [`testing-documentation`](../testing-documentation/) folder located in the root directory of this repository.

This folder contains all necessary information to validate the deployment and functionality of the MODAPTO system.

## Contributors

- Alkis Aznavouridis (<a.aznavouridis@atc.gr>)
