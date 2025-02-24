@echo off
cls

:: MODAPTO Logo
echo.
echo.
echo #############################################################
echo #                                                           #
echo #   M     M   OOOO    DDDD    AAAA   PPPP   TTTTT   OOOO    #
echo #   M M M M  O    O   D   D  A    A  P   P    T    O    O   #
echo #   M  M  M  O    O   D   D  AAAAAA  PPPP     T    O    O   #
echo #   M     M  O    O   D   D  A    A  P        T    O    O   #
echo #   M     M   OOOO    DDDD   A    A  P        T     OOOO    #
echo #                                                           #
echo #############################################################
echo.
echo.
echo ----------------------------------------------
echo Setting up MODAPTO System Deployment...
echo ----------------------------------------------

:: Check if Docker is installed
echo Checking if Docker is installed..
echo ----------------------------------------------
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed. Please install Docker Desktop for Windows from:
    echo https://www.docker.com/products/docker-desktop
    echo After installation, please run this script again.
    pause
    exit /b 1
) else (
    echo Docker is already installed..
)

:: Check if Docker Compose is installed (included with Docker Desktop for Windows)
echo ----------------------------------------------
echo Checking Docker Compose...
docker compose --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Compose not found. Please ensure Docker Desktop is properly installed.
    pause
    exit /b 1
) else (
    echo Docker Compose is already installed..
)

:: Create MODAPTO network
echo ----------------------------------------------
echo Creating MODAPTO network...
docker network inspect modapto > nul 2>&1
if %errorlevel% neq 0 (
    echo ----------------------------------------------
    docker network create modapto
    echo Network created successfully!
) else (
    echo Network already exists..
)

:: Change permissions to specified files
echo ----------------------------------------------
echo Setting appropriate file permissions...
echo ----------------------------------------------
icacls ".\.api-gateway\certs\acme.json" /inheritance:r /grant:r "%USERNAME%:(F)" > nul 2>&1
icacls ".\message-bus\scripts\kafka-init-topics-single-broker.sh" /inheritance:r /grant:r "%USERNAME%:(F)" > nul 2>&1
icacls ".\message-bus\mqtt\config\passwd" /inheritance:r /grant:r "%USERNAME%:(F)" > nul 2>&1
icacls ".\production-knowledge-base\setup\entrypoint.sh" /inheritance:r /grant:r "%USERNAME%:(F)" > nul 2>&1
icacls ".\production-knowledge-base\setup\lib.sh" /inheritance:r /grant:r "%USERNAME%:(F)" > nul 2>&1
echo Permissions set successfully!

:: Starting API Gateway
echo ----------------------------------------------
echo Starting API Gateway component..
docker compose --profile proxy up -d traefik

:: Setup Keycloak
echo ----------------------------------------------
echo Setting up Keycloak and API Gateway to retrieve Client Token...
docker compose up -d postgres_db keycloak

:: Setup ELK Stack
echo ----------------------------------------------
echo Setting up ELK Stack...
docker compose up -d setup

echo ----------------------------------------------
echo Setup completed!
echo ----------------------------------------------
pause