#!/bin/bash
# Convenience script to run the synthetic data generator demo

echo "Running Cylestio Monitor Synthetic Data Generator Demo"
echo "====================================================="
echo

# Run the demo script from the tools directory
cd "$(dirname "$0")/tools/synthetic_data_generator"
./run_demo.sh 