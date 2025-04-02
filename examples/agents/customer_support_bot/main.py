import os
import sqlite3
from enum import Enum
from typing import Annotated, Dict, Sequence, TypedDict

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

import cylestio_monitor

cylestio_monitor.start_monitoring(
    "customer_support_bot", config={"log_file": "output/support_agent.json"}
)

# Load environment variables
load_dotenv()

# Database setup
DB_PATH = "travel.sqlite"


# Initialize database if it doesn't exist
def init_db():
    # Here we'd normally download the DB as in the tutorial
    # For simplicity, we'll just create a simple schema if file doesn't exist
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create some basic tables for demonstration
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            policy TEXT
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY,
            flight_number TEXT,
            origin TEXT,
            destination TEXT,
            scheduled_departure TEXT,
            scheduled_arrival TEXT,
            status TEXT
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY,
            name TEXT,
            location TEXT,
            available_rooms INTEGER,
            price_per_night REAL
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS car_rentals (
            id INTEGER PRIMARY KEY,
            location TEXT,
            vehicle_type TEXT,
            available INTEGER,
            price_per_day REAL
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS excursions (
            id INTEGER PRIMARY KEY,
            name TEXT,
            location TEXT,
            description TEXT,
            price REAL
        )
        """
        )

        # Insert some example data
        policies = [
            (
                1,
                "Cancellation",
                "Flights can be cancelled up to 24 hours before departure for a full refund.",
            ),
            (
                2,
                "Baggage",
                "Each passenger is allowed one carry-on and one checked bag up to 50 pounds.",
            ),
            (
                3,
                "Pets",
                "Small pets under 20 pounds are allowed in the cabin for a $95 fee.",
            ),
        ]
        cursor.executemany("INSERT INTO policies VALUES (?, ?, ?)", policies)

        # Current date for creating example data that will work with recent dates
        import datetime

        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        two_weeks = today + datetime.timedelta(days=14)

        # Format dates as strings with just the date part (to match search queries)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        next_week_str = next_week.strftime("%Y-%m-%d")
        two_weeks_str = two_weeks.strftime("%Y-%m-%d")

        # Add more example flights with dates relative to current date
        flights = [
            # Original flights
            (
                1,
                "AA123",
                "NYC",
                "LAX",
                "2024-05-15 08:00:00",
                "2024-05-15 11:30:00",
                "On Time",
            ),
            (
                2,
                "AA456",
                "LAX",
                "NYC",
                "2024-05-22 09:00:00",
                "2024-05-22 17:30:00",
                "On Time",
            ),
            # New flights with dates relative to current date
            (
                3,
                "BA001",
                "London",
                "New York",
                f"{tomorrow_str} 09:00:00",
                f"{tomorrow_str} 12:30:00",
                "On Time",
            ),
            (
                4,
                "BA002",
                "New York",
                "London",
                f"{next_week_str} 14:00:00",
                f"{next_week_str} 02:30:00",
                "On Time",
            ),
            (
                5,
                "LH100",
                "London",
                "Berlin",
                f"{tomorrow_str} 10:15:00",
                f"{tomorrow_str} 13:45:00",
                "On Time",
            ),
            (
                6,
                "AF200",
                "Paris",
                "Madrid",
                f"{next_week_str} 07:30:00",
                f"{next_week_str} 09:45:00",
                "On Time",
            ),
            (
                7,
                "EK300",
                "Dubai",
                "Sydney",
                f"{two_weeks_str} 23:45:00",
                f"{two_weeks_str} 16:30:00",
                "On Time",
            ),
            (
                8,
                "SQ400",
                "Singapore",
                "Tokyo",
                f"{next_week_str} 08:20:00",
                f"{next_week_str} 16:15:00",
                "On Time",
            ),
            (
                9,
                "TK500",
                "Istanbul",
                "London",
                f"{tomorrow_str} 15:30:00",
                f"{tomorrow_str} 17:45:00",
                "On Time",
            ),
            (
                10,
                "QF600",
                "Sydney",
                "Singapore",
                f"{two_weeks_str} 06:45:00",
                f"{two_weeks_str} 13:20:00",
                "On Time",
            ),
        ]
        cursor.executemany("INSERT INTO flights VALUES (?, ?, ?, ?, ?, ?, ?)", flights)

        # Add example hotels
        hotels = [
            (1, "Grand Plaza Hotel", "London", 10, 250.00),
            (2, "Midtown Suites", "New York", 5, 350.00),
            (3, "Ocean View Resort", "Miami", 15, 200.00),
            (4, "Mountain Retreat", "Denver", 8, 180.00),
            (5, "Sunset Beach Hotel", "Los Angeles", 12, 300.00),
            (6, "Ritz Palace", "Paris", 7, 450.00),
            (7, "Cherry Blossom Inn", "Tokyo", 9, 280.00),
            (8, "Opera House View", "Sydney", 6, 320.00),
            (9, "Canal Suites", "Amsterdam", 11, 220.00),
            (10, "Golden Gate Lodge", "San Francisco", 14, 270.00),
        ]
        cursor.executemany("INSERT INTO hotels VALUES (?, ?, ?, ?, ?)", hotels)

        # Add example car rentals
        car_rentals = [
            (1, "London", "Economy", 5, 40.00),
            (2, "London", "SUV", 3, 80.00),
            (3, "New York", "Economy", 8, 50.00),
            (4, "New York", "Luxury", 2, 120.00),
            (5, "Paris", "Compact", 6, 45.00),
            (6, "Tokyo", "Midsize", 4, 60.00),
            (7, "Sydney", "Van", 2, 90.00),
            (8, "Berlin", "Economy", 7, 35.00),
            (9, "Madrid", "Convertible", 1, 100.00),
            (10, "Rome", "SUV", 3, 75.00),
        ]
        cursor.executemany(
            "INSERT INTO car_rentals VALUES (?, ?, ?, ?, ?)", car_rentals
        )

        # Add example excursions
        excursions = [
            (
                1,
                "London City Tour",
                "London",
                "Comprehensive sightseeing tour of London landmarks",
                50.00,
            ),
            (
                2,
                "Statue of Liberty Visit",
                "New York",
                "Ferry ride and tour of the Statue of Liberty",
                35.00,
            ),
            (
                3,
                "Wine Tasting Tour",
                "Paris",
                "Guided tour of local vineyards with wine tasting",
                70.00,
            ),
            (
                4,
                "Mount Fuji Day Trip",
                "Tokyo",
                "Full-day excursion to Mount Fuji",
                85.00,
            ),
            (
                5,
                "Sydney Harbour Cruise",
                "Sydney",
                "Scenic cruise of Sydney Harbour",
                60.00,
            ),
            (
                6,
                "Berlin Wall Tour",
                "Berlin",
                "Historical tour of the Berlin Wall",
                40.00,
            ),
            (
                7,
                "Sagrada Familia Visit",
                "Barcelona",
                "Guided tour of the Sagrada Familia",
                45.00,
            ),
            (
                8,
                "Safari Adventure",
                "Nairobi",
                "Full-day safari adventure in a national park",
                120.00,
            ),
            (
                9,
                "Grand Canyon Tour",
                "Las Vegas",
                "Helicopter tour of the Grand Canyon",
                250.00,
            ),
            (
                10,
                "Northern Lights Expedition",
                "Reykjavik",
                "Evening tour to view the Northern Lights",
                80.00,
            ),
        ]
        cursor.executemany("INSERT INTO excursions VALUES (?, ?, ?, ?, ?)", excursions)

        conn.commit()
        conn.close()

        print(
            f"Database initialized with example data including flights for tomorrow ({tomorrow_str}), next week ({next_week_str}), and two weeks from now ({two_weeks_str})."
        )


# Initialize database
init_db()


# Define tools
@tool
def lookup_policy(topic: str) -> str:
    """Look up company policies on a specific topic."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT policy FROM policies WHERE topic LIKE ?", (f"%{topic}%",))
    results = cursor.fetchall()

    conn.close()

    if not results:
        return f"No policy found for topic: {topic}."

    policies = [row[0] for row in results]
    return "\n".join(policies)


class FlightSearchInput(BaseModel):
    origin: str = Field(description="Origin airport code or city")
    destination: str = Field(description="Destination airport code or city")
    date: str = Field(description="Date of travel in YYYY-MM-DD format")


@tool
def search_flights(input: FlightSearchInput) -> str:
    """Search for available flights between origin and destination on a given date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(
        f"Searching for flights: {input.origin} to {input.destination} on {input.date}"
    )

    # Extract the date part only from the scheduled_departure for comparison
    cursor.execute(
        "SELECT flight_number, scheduled_departure, scheduled_arrival, status FROM flights "
        "WHERE origin LIKE ? AND destination LIKE ? AND scheduled_departure LIKE ?",
        (f"%{input.origin}%", f"%{input.destination}%", f"{input.date}%"),
    )
    results = cursor.fetchall()

    print(f"Query results: {results}")

    conn.close()

    if not results:
        return f"No flights found from {input.origin} to {input.destination} on {input.date}."

    flights = []
    for row in results:
        flight_num, departure, arrival, status = row
        flights.append(
            f"Flight {flight_num}: Departs {departure}, Arrives {arrival}, Status: {status}"
        )

    return "\n".join(flights)


class BookFlightInput(BaseModel):
    flight_number: str = Field(description="Flight number to book")
    passenger_name: str = Field(description="Name of the passenger")
    contact_info: str = Field(description="Contact information for the passenger")


@tool
def book_flight(input: BookFlightInput) -> str:
    """Book a flight for a passenger."""
    # In a real implementation, this would update the database
    # For demo purposes, we'll just return a confirmation message
    return (
        f"Successfully booked flight {input.flight_number} for {input.passenger_name}."
    )


class HotelSearchInput(BaseModel):
    location: str = Field(description="City or area to search for hotels")
    check_in: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(description="Number of guests")


@tool
def search_hotels(input: HotelSearchInput) -> str:
    """Search for available hotels in a location for given dates and number of guests."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(
        f"Searching for hotels in {input.location} from {input.check_in} to {input.check_out} for {input.guests} guests"
    )

    cursor.execute(
        "SELECT name, available_rooms, price_per_night FROM hotels WHERE location LIKE ?",
        (f"%{input.location}%",),
    )
    results = cursor.fetchall()

    print(f"Query results: {results}")

    conn.close()

    if not results:
        return f"No hotels found in {input.location} for the specified dates."

    hotels = []
    for row in results:
        name, available, price = row
        if available >= input.guests:
            hotels.append(f"{name}: {available} rooms available, ${price} per night")

    if not hotels:
        return f"No hotels found in {input.location} with availability for {input.guests} guests."

    return "\n".join(hotels)


class CarRentalSearchInput(BaseModel):
    location: str = Field(description="City or area to search for car rentals")
    pickup_date: str = Field(description="Pickup date in YYYY-MM-DD format")
    return_date: str = Field(description="Return date in YYYY-MM-DD format")
    vehicle_type: str = Field(description="Type of vehicle (e.g., economy, SUV)")


@tool
def search_car_rentals(input: CarRentalSearchInput) -> str:
    """Search for available car rentals in a location for given dates and vehicle type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(
        f"Searching for {input.vehicle_type} cars in {input.location} from {input.pickup_date} to {input.return_date}"
    )

    cursor.execute(
        "SELECT vehicle_type, available, price_per_day FROM car_rentals "
        "WHERE location LIKE ? AND vehicle_type LIKE ?",
        (f"%{input.location}%", f"%{input.vehicle_type}%"),
    )
    results = cursor.fetchall()

    print(f"Query results: {results}")

    conn.close()

    if not results:
        return f"No {input.vehicle_type} cars found in {input.location} for the specified dates."

    cars = []
    for row in results:
        vehicle, available, price = row
        if available > 0:
            cars.append(f"{vehicle}: {available} available, ${price} per day")

    if not cars:
        return f"No {input.vehicle_type} cars available in {input.location} for the specified dates."

    return "\n".join(cars)


class ExcursionSearchInput(BaseModel):
    location: str = Field(description="City or area to search for excursions")
    date: str = Field(description="Date in YYYY-MM-DD format")
    activity_type: str = Field(
        description="Type of activity (e.g., sightseeing, adventure)"
    )


@tool
def search_excursions(input: ExcursionSearchInput) -> str:
    """Search for available excursions in a location for a given date and activity type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(
        f"Searching for {input.activity_type} excursions in {input.location} on {input.date}"
    )

    cursor.execute(
        "SELECT name, description, price FROM excursions WHERE location LIKE ?",
        (f"%{input.location}%",),
    )
    results = cursor.fetchall()

    print(f"Query results: {results}")

    conn.close()

    if not results:
        return f"No excursions found in {input.location} for {input.date}."

    excursions = []
    for row in results:
        name, description, price = row
        if (
            input.activity_type.lower() in description.lower() or True
        ):  # Include all activities for now
            excursions.append(f"{name}: {description}, ${price}")

    if not excursions:
        return f"No {input.activity_type} excursions found in {input.location} for {input.date}."

    return "\n".join(excursions)


# Create a web search tool using Tavily
web_search = TavilySearchResults(k=3)

# Gather all tools
tools = [
    lookup_policy,
    search_flights,
    book_flight,
    search_hotels,
    search_car_rentals,
    search_excursions,
    web_search,
]

# Initialize the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo")
# Alternatively: llm = ChatAnthropic(model="claude-3-opus-20240229")

# Part 1: Zero-shot Agent


# Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[
        Sequence[BaseMessage], "The messages in the conversation so far"
    ]
    sender: Annotated[str, "The sender of the last message"]


# Create the agent prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful customer support agent for a travel company.
You can help users with questions about company policies, booking flights, hotels, car rentals, and excursions.
If you don't know the answer to a question, you should search for information online.

Use the tools available to assist the user and fulfill their requests.
Always be polite and helpful, and provide detailed information to the user.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create the agent using LangChain's agent framework
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# Define the graph
def run_agent(state: AgentState):
    """Run the agent on the messages and update the state."""
    messages = state["messages"]
    result = agent_executor.invoke({"messages": messages})
    return {
        "messages": messages + [AIMessage(content=result["output"])],
        "sender": "agent",
    }


# Define a function to decide whether to continue or finish
def should_continue(state: AgentState) -> str:
    """Determine whether to continue with the agent or end."""
    sender = state.get("sender")
    return "agent" if sender == "human" else END


# Create the workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", run_agent)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)

# Compile the workflow
part1_agent = workflow.compile()

# Part 2: Add Confirmation


# Define the state for our confirmation agent
class ConfirmationState(TypedDict):
    messages: Annotated[
        Sequence[BaseMessage], "The messages in the conversation so far"
    ]
    sender: Annotated[str, "The sender of the last message"]
    confirmation_needed: Annotated[
        bool, "Whether confirmation is needed for the agent's action"
    ]
    pending_action: Annotated[Dict, "The pending action to be confirmed"]


# Create the confirmation agent prompt
confirmation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful customer support agent for a travel company.
You can help users with questions about company policies, booking flights, hotels, car rentals, and excursions.
Before performing any booking action, you must confirm with the user.

For example, before booking a flight, ask the user to confirm with the details.

Use the tools available to assist the user and fulfill their requests.
Always be polite and helpful, and provide detailed information to the user.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create the confirmation agent
confirmation_agent = create_openai_functions_agent(llm, tools, confirmation_prompt)
confirmation_executor = AgentExecutor(
    agent=confirmation_agent, tools=tools, verbose=True
)


# Function to run the agent and check if confirmation is needed
def run_agent_with_confirmation(state: ConfirmationState):
    """Run the agent and check if confirmation is needed."""
    messages = state["messages"]

    # If we're already in a confirmation flow, check the user's response
    if state.get("confirmation_needed", False) and state["pending_action"]:
        last_message = messages[-1]
        confirmation_text = last_message.content.lower()
        confirmed = any(
            word in confirmation_text
            for word in ["yes", "proceed", "confirm", "go ahead", "ok", "okay"]
        )

        if confirmed:
            # Add confirmation message to the conversation
            confirm_msg = AIMessage(
                content="Thank you for confirming. I'll proceed with your request now."
            )
            messages.append(confirm_msg)

            # Get the pending action result
            result = confirmation_executor.invoke({"messages": messages})
            return {
                "messages": messages + [AIMessage(content=result["output"])],
                "sender": "agent",
                "confirmation_needed": False,
                "pending_action": {},
            }
        else:
            # User declined
            decline_msg = AIMessage(
                content="I understand. I won't proceed with that action. Is there something else you'd like help with?"
            )
            return {
                "messages": messages + [decline_msg],
                "sender": "agent",
                "confirmation_needed": False,
                "pending_action": {},
            }

    # Otherwise, run the agent
    result = confirmation_executor.invoke({"messages": messages})
    output = result["output"]

    # Check if this is a booking action that needs confirmation
    booking_indicators = ["book", "reserve", "confirm", "purchase", "buy"]
    booking_actions = ["flight", "hotel", "car", "rental", "excursion", "trip"]

    needs_confirmation = False
    for indicator in booking_indicators:
        if indicator in output.lower():
            for action in booking_actions:
                if action in output.lower():
                    needs_confirmation = True
                    break
            if needs_confirmation:
                break

    if needs_confirmation:
        # Format a confirmation message
        confirmation_msg = AIMessage(
            content=f"{output}\n\nWould you like me to proceed with this booking? Please confirm."
        )

        return {
            "messages": messages + [confirmation_msg],
            "sender": "agent",
            "confirmation_needed": True,
            "pending_action": {"action": output},
        }

    # No confirmation needed
    return {
        "messages": messages + [AIMessage(content=output)],
        "sender": "agent",
        "confirmation_needed": False,
        "pending_action": {},
    }


# Define a function to route the flow
def route_confirmation(state: ConfirmationState) -> str:
    """Route the confirmation flow."""
    sender = state.get("sender")

    if sender == "human":
        return "agent"

    return END


# Create the confirmation workflow
confirmation_workflow = StateGraph(ConfirmationState)
confirmation_workflow.add_node("agent", run_agent_with_confirmation)
confirmation_workflow.set_entry_point("agent")
confirmation_workflow.add_conditional_edges("agent", route_confirmation)

# Compile the confirmation workflow
part2_agent = confirmation_workflow.compile()

# Part 3: Conditional Interrupt


# Define the state for our interrupt agent
class InterruptState(TypedDict):
    messages: Annotated[
        Sequence[BaseMessage], "The messages in the conversation so far"
    ]
    sender: Annotated[str, "The sender of the last message"]
    interrupted: Annotated[bool, "Whether the flow has been interrupted"]
    escalate_human: Annotated[bool, "Whether to escalate to a human agent"]


# Create the interrupt agent prompt
interrupt_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful customer support agent for a travel company.
You can help users with questions about company policies, booking flights, hotels, car rentals, and excursions.
If a user asks to speak to a human agent or has a complex issue that you cannot resolve, you should escalate to a human agent.

Use the tools available to assist the user and fulfill their requests.
Always be polite and helpful, and provide detailed information to the user.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create the interrupt agent
interrupt_agent = create_openai_functions_agent(llm, tools, interrupt_prompt)
interrupt_executor = AgentExecutor(agent=interrupt_agent, tools=tools, verbose=True)


# Function to check if the user wants to speak to a human
def check_for_human_request(state: InterruptState):
    """Check if the user is requesting a human agent."""
    messages = state["messages"]
    if not messages:
        return state

    last_message = messages[-1]
    if last_message.type == "human":
        content = last_message.content.lower()
        human_requests = [
            "speak to a human",
            "talk to a person",
            "human agent",
            "real person",
            "supervisor",
            "manager",
        ]

        if any(request in content for request in human_requests):
            interrupt_msg = AIMessage(
                content="I understand you'd like to speak with a human agent. I'm connecting you with one of our customer service representatives. Please hold."
            )
            return {
                "messages": messages + [interrupt_msg],
                "sender": "agent",
                "interrupted": True,
                "escalate_human": True,
            }

    return state


# Function to run the agent with interrupt checking
def run_agent_with_interrupt(state: InterruptState):
    """Run the agent with interrupt checking."""
    # Check if human escalation is requested
    state = check_for_human_request(state)
    if state.get("escalate_human", False):
        return state

    # Otherwise, run the normal agent
    messages = state["messages"]
    result = interrupt_executor.invoke({"messages": messages})

    return {
        "messages": messages + [AIMessage(content=result["output"])],
        "sender": "agent",
        "interrupted": False,
        "escalate_human": False,
    }


# Define a function to route the interrupt flow
def route_interrupt(state: InterruptState) -> str:
    """Route the interrupt flow."""
    sender = state.get("sender")

    if state.get("escalate_human", False):
        return "human_agent"  # This would be a node that handles human escalation

    if sender == "human":
        return "agent"

    return END


# Mock human agent handling function
def human_agent_handler(state: InterruptState):
    """Handle escalation to a human agent."""
    messages = state["messages"]
    human_msg = AIMessage(
        content="[Human Agent] Hello, this is a customer service representative. How can I assist you today?"
    )

    return {
        "messages": messages + [human_msg],
        "sender": "human_agent",
        "interrupted": True,
        "escalate_human": True,
    }


# Create the interrupt workflow
interrupt_workflow = StateGraph(InterruptState)
interrupt_workflow.add_node("agent", run_agent_with_interrupt)
interrupt_workflow.add_node("human_agent", human_agent_handler)
interrupt_workflow.set_entry_point("agent")
interrupt_workflow.add_conditional_edges("agent", route_interrupt)
interrupt_workflow.add_conditional_edges("human_agent", lambda _: END)

# Compile the interrupt workflow
part3_agent = interrupt_workflow.compile()

# Part 4: Specialized Workflows


# Define different types of assistants for specialized workflows
class AssistantType(str, Enum):
    GENERAL = "general"
    FLIGHT = "flight"
    HOTEL = "hotel"
    CAR = "car"
    EXCURSION = "excursion"


# Define the state for our specialized workflow
class SpecializedState(TypedDict):
    messages: Annotated[
        Sequence[BaseMessage], "The messages in the conversation so far"
    ]
    sender: Annotated[str, "The sender of the last message"]
    assistant_type: Annotated[AssistantType, "The type of assistant to use"]


# Create specialized assistant prompts
general_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful general customer support agent for a travel company.
You can help users with questions about company policies and direct them to specialized agents for booking flights, hotels, car rentals, and excursions.

Use the tools available to assist the user and fulfill their requests.
If the user wants to book a flight, hotel, car, or excursion, make sure to note that.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

flight_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a flight booking specialist for a travel company.
You can help users search for and book flights.

Use the tools available to assist the user and fulfill their requests.
Always provide detailed information about flight options and confirm booking details with the user before finalizing.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

hotel_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a hotel booking specialist for a travel company.
You can help users search for and book hotels.

Use the tools available to assist the user and fulfill their requests.
Always provide detailed information about hotel options and amenities.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

car_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a car rental specialist for a travel company.
You can help users search for and book car rentals.

Use the tools available to assist the user and fulfill their requests.
Always provide detailed information about car options and rental policies.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

excursion_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an excursion booking specialist for a travel company.
You can help users search for and book excursions and activities.

Use the tools available to assist the user and fulfill their requests.
Always provide detailed information about excursion options, duration, and what's included.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create specialized assistants
general_agent = create_openai_functions_agent(
    llm, [lookup_policy, web_search], general_prompt
)
general_executor = AgentExecutor(
    agent=general_agent, tools=[lookup_policy, web_search], verbose=True
)

flight_agent = create_openai_functions_agent(
    llm, [search_flights, book_flight], flight_prompt
)
flight_executor = AgentExecutor(
    agent=flight_agent, tools=[search_flights, book_flight], verbose=True
)

hotel_agent = create_openai_functions_agent(llm, [search_hotels], hotel_prompt)
hotel_executor = AgentExecutor(agent=hotel_agent, tools=[search_hotels], verbose=True)

car_agent = create_openai_functions_agent(llm, [search_car_rentals], car_prompt)
car_executor = AgentExecutor(agent=car_agent, tools=[search_car_rentals], verbose=True)

excursion_agent = create_openai_functions_agent(
    llm, [search_excursions], excursion_prompt
)
excursion_executor = AgentExecutor(
    agent=excursion_agent, tools=[search_excursions], verbose=True
)


# Function to determine the assistant type based on the message
def determine_assistant_type(state: SpecializedState):
    """Determine which assistant type should handle the message."""
    messages = state["messages"]
    if not messages:
        return state

    last_message = messages[-1]
    if last_message.type != "human":
        return state

    content = last_message.content.lower()

    # Simple keyword matching for demonstration
    if any(
        word in content for word in ["flight", "fly", "plane", "airport", "airline"]
    ):
        return {**state, "assistant_type": AssistantType.FLIGHT}
    elif any(
        word in content for word in ["hotel", "motel", "stay", "room", "accommodation"]
    ):
        return {**state, "assistant_type": AssistantType.HOTEL}
    elif any(word in content for word in ["car", "vehicle", "rent", "rental", "drive"]):
        return {**state, "assistant_type": AssistantType.CAR}
    elif any(
        word in content
        for word in ["excursion", "tour", "activity", "sightseeing", "visit"]
    ):
        return {**state, "assistant_type": AssistantType.EXCURSION}

    return {**state, "assistant_type": AssistantType.GENERAL}


# Function to create a new assistant based on the assistant_type
def create_assistant(state: SpecializedState):
    """Create an assistant based on the assistant_type."""
    assistant_type = state.get("assistant_type", AssistantType.GENERAL)
    messages = state["messages"]

    # Determine which executor to use based on assistant_type
    if assistant_type == AssistantType.FLIGHT:
        result = flight_executor.invoke({"messages": messages})
    elif assistant_type == AssistantType.HOTEL:
        result = hotel_executor.invoke({"messages": messages})
    elif assistant_type == AssistantType.CAR:
        result = car_executor.invoke({"messages": messages})
    elif assistant_type == AssistantType.EXCURSION:
        result = excursion_executor.invoke({"messages": messages})
    else:
        result = general_executor.invoke({"messages": messages})

    return {
        "messages": messages + [AIMessage(content=result["output"])],
        "sender": "agent",
        "assistant_type": assistant_type,
    }


# Define a function to route the specialized workflow
def route_specialized(state: SpecializedState) -> str:
    """Route the specialized workflow."""
    sender = state.get("sender")

    if sender == "human":
        return "determine_assistant_type"

    return END


# Create the specialized workflow
specialized_workflow = StateGraph(SpecializedState)
specialized_workflow.add_node("determine_assistant_type", determine_assistant_type)
specialized_workflow.add_node("create_assistant", create_assistant)
specialized_workflow.set_entry_point("determine_assistant_type")
specialized_workflow.add_edge("determine_assistant_type", "create_assistant")
specialized_workflow.add_conditional_edges("create_assistant", route_specialized)

# Compile the specialized workflow
part4_agent = specialized_workflow.compile()

# Export agents for use
agents = {
    "part1": part1_agent,
    "part2": part2_agent,
    "part3": part3_agent,
    "part4": part4_agent,
}

if __name__ == "__main__":
    # Choose which agent to run
    agent = part4_agent  # Change to part1_agent, part2_agent, part3_agent as needed

    # Simple chat loop
    messages = []

    print("Customer Support Bot (type 'exit' to quit)")
    print("-------------------------------------------")

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            cylestio_monitor.stop_monitoring()
            break

        # Add the user message to the conversation
        user_message = HumanMessage(content=user_input)
        messages.append(user_message)

        # Invoke the agent
        result = agent.invoke({"messages": messages, "sender": "human"})

        # Update the messages
        messages = result["messages"]

        # Print the agent's response
        for message in messages:
            if message.type == "ai" and messages.index(message) >= len(messages) - 2:
                print(f"Agent: {message.content}")
