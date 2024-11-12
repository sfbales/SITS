# SITS - Snake In The Shell

## Overview
SITS (Snake In The Shell) is a suite designed for managing Python-based software, providing tools for package management, command execution, script scheduling, API exposure, and more. This guide helps you set up and run the program, including instructions on configuring ngrok for API access.

---

## Requirements

1. **Python**: Ensure Python 3.7 or higher is installed.
2. **Dependencies**: Install required packages using:

    ```bash
    pip install -r requirements.txt
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
