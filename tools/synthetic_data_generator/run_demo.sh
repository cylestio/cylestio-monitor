#!/bin/bash
# Run the Cylestio Monitor synthetic data generation and visualization

echo "Cylestio Monitor Demo"
echo "===================="
echo

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
    echo "Error: Python 3.11 or higher is required."
    echo "Current version: $python_version"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing dependencies. Please check requirements.txt."
    exit 1
fi

# Generate synthetic data
echo
echo "Generating synthetic data..."
./generate_synthetic_data.py
if [ $? -ne 0 ]; then
    echo "Error generating synthetic data."
    exit 1
fi

# Test the generated data
echo
echo "Testing generated data..."
./test_data_generation.py
if [ $? -ne 0 ]; then
    echo "Warning: Some tests failed. The data may not be as expected."
    # Continue anyway
fi

# Visualize the data
echo
echo "Generating visualizations..."
./visualize_data.py
if [ $? -ne 0 ]; then
    echo "Error generating visualizations."
    exit 1
fi

echo
echo "Demo completed successfully!"
echo "Check the current directory for visualization PNG files."
echo "The synthetic data is stored in ~/.cylestio/monitor.db" 