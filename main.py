from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic.v1 import BaseModel, Field, validator
from langchain.chains import LLMChain
from typing import List, Dict, Optional, Literal, Union, Any
import psycopg2
import json
import decimal
from config import get_db_connection, OLLAMA_BASE_URL, MODEL_NAME, CURRENCY, CURRENCY_SYMBOL

# Define structured output models using Pydantic
class GroceryItem(BaseModel):
    name: str
    quantity: float
    unit: str
    unit_price: float
    amount: float
    calculation: str = Field(description="Step-by-step calculation explanation")

class ShoppingList(BaseModel):
    items: List[GroceryItem]
    total: float
    
    @validator('total')
    def validate_total(cls, total, values):
        """Validate that the total matches the sum of item amounts"""
        if 'items' in values:
            calculated_total = sum(item.amount for item in values['items'])
            # Check with a small tolerance for floating-point issues
            if abs(total - calculated_total) > 0.01:
                # Auto-correct the total
                return calculated_total
        return total

class CategoryListing(BaseModel):
    category: str
    items: List[Dict[str, Any]]

class QueryType(BaseModel):
    type: Literal["price_query", "shopping_list", "category_query", "comparison_query", "unknown"]
    explanation: str = Field(description="Explanation of why this query type was selected")

def create_app():
    """
    Initialize the improved Grocery Price Assistant using structured LangChain components.
    """
    print("Initializing Grocery Price Assistant...")
    print(f"Using model: {MODEL_NAME}")
    print(f"Prices stored in: {CURRENCY}")
    
    # Load all grocery items from database
    grocery_items = load_all_grocery_items()
    
    # Handle Decimal serialization
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    grocery_items_json = json.dumps(grocery_items, indent=2, default=decimal_default)
    print(f"Loaded {len(grocery_items)} grocery items into memory")
    
    # Create a dictionary lookup for faster item access
    item_lookup = {item['name'].lower(): item for item in grocery_items}
    
    # Initialize LLM with more precise settings
    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=MODEL_NAME,
        temperature=0,  # Zero temperature for deterministic outputs
    )
    
    # 1. Query Classifier Chain
    query_classifier_prompt = ChatPromptTemplate.from_template("""
    Your task is to classify the user's grocery-related query into one of these types:
    - price_query: User wants to know the price of specific items
    - shopping_list: User wants to calculate the total cost of multiple items with quantities
    - category_query: User wants to see all items in a specific category
    - comparison_query: User wants to compare prices between items
    - unknown: Query doesn't fit any of the above categories

    User query: {question}

    Respond with a JSON object containing the type and an explanation.
    """)
    
    query_classifier_parser = JsonOutputParser()
    
    query_classifier_chain = query_classifier_prompt | llm | query_classifier_parser
    
    # 2. Price Query Chain
    price_query_prompt = ChatPromptTemplate.from_template("""
    You are a grocery price lookup assistant. The user wants to know the price of specific items.
    
    Here is the complete list of grocery items with their prices and units:
    {grocery_items}
    
    User query: {question}
    
    Find the exact matching item(s) in the database and provide their prices.
    State the price per unit clearly: e.g., "Milk costs ₹65 per liter"
    Do not convert units or perform calculations unless specifically requested.
    
    ONLY respond with the price information, nothing else.
    """)
    
    price_query_chain = price_query_prompt | llm | StrOutputParser()
    
    # 3. Shopping List Chain
    shopping_list_prompt = ChatPromptTemplate.from_template("""
    You are a precise grocery shopping calculator. Extract the items and quantities from the query.
    
    Here is the complete list of grocery items with their prices and units:
    {grocery_items}
    
    User query: {question}
    
    For each item mentioned in the query:
    1. Find the exact matching item in the database (do not guess or invent items)
    2. Extract the quantity requested
    3. Calculate the exact cost based on the requested quantity and unit
    4. For weight conversions: 1 kg = 1000 g
    5. For volume conversions: 1 liter = 1000 ml
    6. Show a clear calculation for each item
    
    IMPORTANT: Be precise with your math calculations. Double-check all arithmetic.
    
    Format your response as a detailed calculation with:
    - A table showing Item, Unit Price, Quantity, and Amount for each item
    - Step-by-step calculations below the table
    - The total sum at the end
    """)
    
    shopping_list_chain = shopping_list_prompt | llm | StrOutputParser()
    
    # 4. Category Query Chain
    category_query_prompt = ChatPromptTemplate.from_template("""
    You are a grocery category lookup assistant. The user wants to see items in a specific category.
    
    Here is the complete list of grocery items with their prices and units:
    {grocery_items}
    
    User query: {question}
    
    1. Identify which category the user is asking about
    2. List all items in that category with their prices
    3. Format each item as: "[Item]: ₹[price] per [unit]"
    
    If the requested category doesn't exist, list the available categories instead.
    """)
    
    category_query_chain = category_query_prompt | llm | StrOutputParser()
    
    # 5. Comparison Query Chain
    comparison_query_prompt = ChatPromptTemplate.from_template("""
    You are a grocery price comparison assistant. The user wants to compare prices between items.
    
    Here is the complete list of grocery items with their prices and units:
    {grocery_items}
    
    User query: {question}
    
    1. Identify the items being compared
    2. Find their prices and units in the database
    3. Convert to the same unit if needed for fair comparison
    4. Clearly state which item is cheaper/more expensive
    5. Show your calculations for the comparison
    
    Be precise with your comparisons and make sure to account for different units.
    """)
    
    comparison_query_chain = comparison_query_prompt | llm | StrOutputParser()
    
    def get_answer(question: str) -> str:
        """Process a natural language question and return an answer about grocery prices"""
        try:
            # First, classify the query type
            query_type_result = query_classifier_chain.invoke({
                "question": question
            })
            
            query_type = query_type_result.get("type", "unknown")
            
            # Handle different query types with specialized chains
            if query_type == "price_query":
                return price_query_chain.invoke({
                    "question": question,
                    "grocery_items": grocery_items_json
                })
                
            elif query_type == "shopping_list":
                return shopping_list_chain.invoke({
                    "question": question,
                    "grocery_items": grocery_items_json
                })
                
            elif query_type == "category_query":
                return category_query_chain.invoke({
                    "question": question,
                    "grocery_items": grocery_items_json
                })
                
            elif query_type == "comparison_query":
                return comparison_query_chain.invoke({
                    "question": question,
                    "grocery_items": grocery_items_json
                })
                
            else:  # unknown or fallback
                return fallback_response(question, grocery_items_json, llm)
                
        except Exception as e:
            # Fallback to the general method if any error occurs
            print(f"Error in query processing: {str(e)}")
            return fallback_response(question, grocery_items_json, llm)

    # General fallback response method
    def fallback_response(question, grocery_items_json, llm):
        """Generate a response using the general-purpose method as a fallback"""
        response_prompt = ChatPromptTemplate.from_template(
            """You are a grocery shopping assistant who helps calculate prices based on grocery items database.

Here is the complete list of grocery items with their prices and units:
{grocery_items}

The user's query is: {question}

First, identify which grocery items from the database are relevant to the query, and then:

1. For price queries:
   - Look up the price of each item from the database
   - State the price per unit clearly: e.g., "Milk costs ₹65 per liter"

2. For shopping list queries (user wants to buy items with quantities):
   - Create a formatted table with columns: Item | Unit Price | Quantity | Amount
   - For each item, calculate the exact cost based on the requested quantity
   - For weight conversions: 1 kg = 1000 g 
   - For volume conversions: 1 liter = 1000 ml
   - Show calculation steps: e.g., "Rice: ₹75/kg × 0.75kg = ₹56.25"
   - Sum up the total at the end
   - DOUBLE-CHECK YOUR MATH: Verify that all calculations are correct

3. For category queries:
   - List all items in the specified category with their prices
   - Format each item as: "[Item]: ₹[price] per [unit]"

4. For comparison queries:
   - Convert to the same unit before comparing (if needed)
   - Clearly state which item is cheaper/more expensive

IMPORTANT: Only use the exact prices and units from the provided grocery items data.
Do NOT invent or assume any information not present in the database.
"""
        )
        
        response_chain = response_prompt | llm | StrOutputParser()
        
        return response_chain.invoke({
            "question": question,
            "grocery_items": grocery_items_json
        })
    
    return get_answer

def load_all_grocery_items():
    """Load all grocery items from the database."""
    try:
        # Connect to database
        conn = psycopg2.connect(**get_db_connection())
        cursor = conn.cursor()
        
        # Fetch all grocery items
        cursor.execute("SELECT * FROM grocery_items;")
        columns = [desc[0] for desc in cursor.description]
        items = cursor.fetchall()
        
        # Convert to list of dictionaries
        grocery_items = []
        for item in items:
            item_dict = dict(zip(columns, item))
            grocery_items.append(item_dict)
        
        # Close connection
        cursor.close()
        conn.close()
        
        return grocery_items
    except Exception as e:
        print(f"Error loading grocery items: {str(e)}")
        return []

def main():
    """Main function to run the Grocery Price Assistant."""
    print("Welcome to the Grocery Price Assistant!")
    print(f"All prices are listed in {CURRENCY} ({CURRENCY_SYMBOL})")
    print("Ask me about the prices of grocery items, or type 'exit' to quit.")
    print("Example: 'I want to buy 2L milk, 1kg tomatoes, and 3 packets of bread'")
    
    # Create the application
    get_answer = create_app()
    
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Thank you for using the Grocery Price Assistant. Goodbye!")
            break
        
        if not user_input.strip():
            continue
            
        response = get_answer(user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    main()