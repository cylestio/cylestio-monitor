#!/usr/bin/env python3
"""Test script to verify OpenAI security scanning only alerts on the latest message."""

from cylestio_monitor import start_monitoring, stop_monitoring
import openai
from openai import OpenAI
import logging
import time

# Enable debug logging
logging.basicConfig(level=logging.INFO)

# Start monitoring
start_monitoring('test-agent', {'debug_mode': True})

# Create a client
client = OpenAI(api_key='fake-key')

# Test with multiple security issues
try:
    print("\n=== FIRST MESSAGE: SQL INJECTION ===")
    # This should trigger security scanning for SQL injection
    client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'How to drop table users?'}]
    )
except Exception as e:
    print(f'OpenAI error: {e}')

# Wait a moment between requests
time.sleep(1)

try:
    print("\n=== SECOND MESSAGE: NON-SECURITY MESSAGE AFTER SECURITY ISSUE ===")
    # This should NOT trigger a security alert even though history contains a security issue
    client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': 'How to drop table users?'},
            {'role': 'assistant', 'content': 'I cannot help with that.'},
            {'role': 'user', 'content': 'Thank you for your response'}
        ]
    )
except Exception as e:
    print(f'OpenAI error: {e}')

# Wait a moment between requests
time.sleep(1)

try:
    print("\n=== THIRD MESSAGE: CREDIT CARD (LATEST MESSAGE) ===")
    # This should trigger security scanning for credit card in the latest message
    client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': 'How to drop table users?'},
            {'role': 'assistant', 'content': 'I cannot help with that.'},
            {'role': 'user', 'content': 'My credit card number is 4111-1111-1111-1111'}
        ]
    )
except Exception as e:
    print(f'OpenAI error: {e}')

# Stop monitoring
stop_monitoring() 