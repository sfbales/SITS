# SITS - Snake In The Shell

## Overview
SITS (Snake In The Shell) is a Python-based suite designed to empower developers and system administrators with powerful tools for automating, managing, and executing scripts. With a GUI-based approach, SITS integrates functionalities like script scheduling, API exposure, command execution, and dependency management, making it an all-in-one toolkit for Python-based system management and automation tasks.

Whether you’re a developer looking to automate repetitive tasks, an administrator managing scripts across different systems, or an enthusiast exploring script scheduling, SITS provides an accessible and flexible platform.
Features

    Dependency Management: Check for required packages, install dependencies, and manage environment configurations.
    Command Management: Organize, save, and execute shell commands from a single interface.
    Script Execution: Load and run Python scripts with dependency checks and management.
    Task Scheduling: Schedule scripts or commands to run at specified times with automatic logging.
    API Exposure: Expose your functionalities as a FastAPI-based REST API, accessible locally or over the internet via ngrok.


---

## Installing

**Python**: Ensure Python 3.7 or higher is installed.

 ```bash
    git clone https://github.com/username/SITSv1.0.git
cd SITSv1.0
 ```

**Dependencies**: Install required packages using:

    ```bash
    pip install -r requirements.txt
    ```
**Run**: 

 ```bash
    chmod +x run.sh
 ```
 ```bash
    ./run.sh
 ```

    This installs all necessary libraries, including FastAPI, psutil, requests, and others.
3. **Tkinter** (for Linux):
    - Install tkinter if it isn’t already installed using:

    ```bash
    sudo apt-get install python3-tk
    ```

---

## Setting Up ngrok

ngrok is used to expose your local FastAPI server to the internet. Follow these steps to set it up:

### Step 1: Download and Install ngrok
1. Visit [ngrok's download page](https://ngrok.com/download) and download the version for your operating system.
2. Extract the downloaded file and place the `ngrok` binary in a directory included in your system’s PATH.

### Step 2: Create an ngrok Account and Get an Auth Token
1. Go to [ngrok's signup page](https://ngrok.com/signup) and create a free account.
2. After signing up, retrieve your auth token from your [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).


### Step 3: Configure SITS for ngrok

1. Open the SITS application and go to the **API Manager** tab.
2. Enter your ngrok token in the provided field and click **Save Token**.
3. Start the API by clicking **Start API**.

The application will provide a public URL once ngrok establishes the tunnel, making your API accessible over the internet.

---

## API Documentation (openapi.json)


Once the server is running, access the OpenAPI schema at `http://127.0.0.1:8000/openapi.json` and save it as `openapi.json` in your project directory.

I've also included a copy of openapi.json in the program folder
