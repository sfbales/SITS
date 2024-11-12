#!/bin/bash

# Activate the virtual environment
source /home/sfb/env/bin/activate

# Define required dependencies
REQUIRED_PACKAGES=("tkinter" "queue" "subprocess" "ast" "json" "threading")

# Function to check and install missing packages
install_missing_packages() {
    MISSING_PACKAGES=()
    for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
        python3 -c "import $PACKAGE" 2>/dev/null
        if [ $? -ne 0 ]; then
            MISSING_PACKAGES+=("$PACKAGE")
        fi
    done

    # Install missing packages if any
    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        echo "Installing missing packages: ${MISSING_PACKAGES[@]}"
        for PACKAGE in "${MISSING_PACKAGES[@]}"; do
            pip install "$PACKAGE"
        done
    else
        echo "All required packages are already installed."
    fi
}

# Check for and install missing dependencies
install_missing_packages

# Run the unified GUI application and redirect logs to the terminal
exec python3 /home/sfb/Desktop/SITSv1.0/sits.py

