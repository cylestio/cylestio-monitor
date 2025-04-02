# Customer Support Bot

This is an implementation of a customer support bot for a travel company, based on the [LangGraph tutorial](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/).

## Features

The bot can assist users with:
- Looking up company policies
- Searching for and booking flights
- Searching for hotels
- Searching for car rentals
- Searching for excursions
- Web search for additional information

## Implementation Details

The implementation includes four increasingly sophisticated versions of the assistant:

1. **Part 1: Zero-shot Agent** - A basic agent that can use tools to answer user queries
2. **Part 2: Confirmation Agent** - Adds confirmation before performing any booking actions
3. **Part 3: Conditional Interrupt** - Adds the ability to detect when a user wants to speak to a human
4. **Part 4: Specialized Workflows** - Routes queries to specialized assistants based on topic

## Requirements

- Python 3.8+
- Dependencies:
  - langgraph
  - langchain-community
  - langchain-anthropic
  - langchain-openai
  - tavily-python
  - pandas
  - dotenv

## Setup

1. Ensure you have the necessary API keys in your `.env` file:
   - `OPENAI_API_KEY` - For using OpenAI models
   - `TAVILY_API_KEY` - For web search functionality
   - `ANTHROPIC_API_KEY` (optional) - If you want to use Claude models

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Example Data

The bot comes with an SQLite database that's automatically populated with sample data on first run. Here's what's included:

### Flights
The database includes flights with dynamic dates based on when you run the bot:
- Flights for tomorrow: London to New York, London to Berlin, Istanbul to London
- Flights for next week: New York to London, Paris to Madrid, Singapore to Tokyo
- Flights for two weeks from now: Dubai to Sydney, Sydney to Singapore
- Static flights: NYC to LAX (May 15, 2024), LAX to NYC (May 22, 2024)

### Hotels
Example hotels in various cities:
- London: Grand Plaza Hotel (10 rooms, $250/night)
- New York: Midtown Suites (5 rooms, $350/night)
- Paris: Ritz Palace (7 rooms, $450/night)
- Tokyo: Cherry Blossom Inn (9 rooms, $280/night)
- And hotels in Miami, Denver, Los Angeles, Sydney, Amsterdam, and San Francisco

### Car Rentals
Example car rentals in various cities:
- London: Economy ($40/day), SUV ($80/day)
- New York: Economy ($50/day), Luxury ($120/day)
- And cars in Paris, Tokyo, Sydney, Berlin, Madrid, and Rome

### Excursions
Example tours and activities:
- London: London City Tour ($50)
- New York: Statue of Liberty Visit ($35)
- Paris: Wine Tasting Tour ($70)
- And activities in Tokyo, Sydney, Berlin, Barcelona, Nairobi, Las Vegas, and Reykjavik

## Usage

Run the main script:

```
python run.py [--agent {1,2,3,4}]
```

Where the --agent argument specifies which version to run:
1. Zero-shot Agent
2. Confirmation Agent
3. Conditional Interrupt Agent
4. Specialized Workflows Agent (default)

## Example Queries

Here are some example queries you can try:

### Flight Queries
```
Do you have any flights from London to New York tomorrow?
Search for flights from Paris to Madrid next week.
Can I book a flight from NYC to LAX on May 15, 2024?
```

### Hotel Queries
```
Find me a hotel in London for 2 guests.
What hotels do you have in Tokyo?
I need a hotel in Paris for next weekend.
```

### Car Rental Queries
```
I need to rent a car in London.
Show me luxury car options in New York.
Are there any economy cars available in Berlin?
```

### Excursion Queries
```
What tours are available in London?
I want to do sightseeing in Tokyo.
Show me activities in Sydney.
```

### Policy Queries
```
What's your baggage policy?
Tell me about your cancellation policy.
What's your policy on pets?
```

## License

MIT
