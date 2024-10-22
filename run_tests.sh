#!/bin/bash

# run_all_tests.sh
# Script to run tests in all plugin directories, or a specific plugin if specified

PLUGIN_DIR="./plugins"
EXIT_CODE=0

# Check if a plugin name was provided as an argument
if [ -n "$1" ]; then
    PLUGIN_NAME="$1"
    PLUGIN_PATH="$PLUGIN_DIR/$PLUGIN_NAME"
    TEST_PATH="$PLUGIN_PATH/tests"
    echo "Running tests for plugin: $PLUGIN_NAME"

    # Check if the specified plugin has a non-empty tests directory
    if [ -d "$TEST_PATH" ] && [ "$(ls -A $TEST_PATH)" ]; then
        echo "-------------------------------------"
        echo "Running tests in $TEST_PATH"
        echo "-------------------------------------"
        
        # Set PYTHONPATH to the parent directory of plugins
        export PYTHONPATH="$PLUGIN_DIR:$PYTHONPATH"
        
        # Run pytest in the specified plugin's tests directory
        pytest "$TEST_PATH"
        
        # Check if pytest command failed
        if [ $? -ne 0 ]; then
            EXIT_CODE=1
        fi
    else
        echo "No tests found in $TEST_PATH. Skipping..."
    fi

else
    echo "Running tests in all plugins under $PLUGIN_DIR..."

    # Loop through all subdirectories in the plugins directory
    for plugin in "$PLUGIN_DIR"/*; do
        PLUGIN_PATH="$plugin"
        TEST_DIR="$PLUGIN_PATH/tests"
        
        # Check if the 'tests' directory exists and is not empty
        if [ -d "$TEST_DIR" ] && [ "$(ls -A $TEST_DIR)" ]; then
            echo "-------------------------------------"
            echo "Running tests in $TEST_DIR"
            echo "-------------------------------------"
            
            # Set PYTHONPATH to the parent directory of plugins
            export PYTHONPATH="$PLUGIN_DIR:$PYTHONPATH"
            
            # Run pytest in the tests directory
            pytest "$TEST_DIR"
            
            # Check if pytest command failed
            if [ $? -ne 0 ]; then
                EXIT_CODE=1
            fi
        else
            echo "No tests found in $TEST_DIR. Skipping..."
        fi
    done
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed. Please check the output above."
fi

exit $EXIT_CODE
