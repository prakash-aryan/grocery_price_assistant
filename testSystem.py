import sys
import datetime
from main import create_app

def run_tests():
    """
    Run multiple test queries through the grocery price assistant
    and save results to a file for analysis.
    """
    # Initialize the application
    print("Initializing the Grocery Price Assistant for testing...")
    get_answer = create_app()
    
    # Define test prompts with expected answers
    test_prompts = [
        # Basic price queries
        "What is the price of milk?",  # Expected: ₹65 per liter
        "How much do tomatoes cost?",  # Expected: ₹40 per kg
        
        # Simple quantity calculations
        "Calculate price for 2 liters of milk",  # Expected: ₹130
        "I want to buy 500g rice",  # Expected: ₹37.5 (half of ₹75)
        
        # Multiple items
        "Calculate 2kg rice and 3 packets of bread",  # Expected: ₹150 (rice) + ₹120 (bread) = ₹270
        "Price for 300g paneer, 400g curd, and 50g green chillies",  # Expected: ₹120 + ₹36 + ₹7.5 = ₹163.5
        
        # Unit conversions
        "I want to buy 500ml cooking oil and 3.5L milk",  # Expected: ₹90 + ₹227.5 = ₹317.5
        "Price for 0.25kg sugar and 1.5 liter cooking oil",  # Expected: ₹11.25 + ₹270 = ₹281.25
        
        # Comparisons
        "Which is more expensive per kg, apples or tomatoes?",  # Expected: Apples (₹180 vs ₹40)
        "Compare the prices of rice and atta per kg",  # Expected: Rice is more expensive (₹75 vs ₹60)
        
        # Budget calculations
        "If I have ₹500, how many kg of potatoes can I buy?",  # Expected: 16.67 kg (₹500/₹30)
        "With ₹300, how many packets of bread and liters of milk can I buy?",  # This is open-ended
        
        # Mixed formulations
        "Price for 100g paneer and 200g green chillies",  # Expected: ₹40 + ₹30 = ₹70
        "I need 250 grams of sugar and three dozen bananas",  # Expected: ₹11.25 + ₹180 = ₹191.25
        
        # Edge cases
        "What items can I buy in the dairy category?",  # Should list dairy items
        "What's the most expensive item in your inventory?",  # Should identify Chicken Breast at ₹320/kg
    ]
    
    # Run tests and collect results
    results = []
    
    print(f"Running {len(test_prompts)} test queries...")
    for i, prompt in enumerate(test_prompts, 1):
        print(f"Testing prompt {i}/{len(test_prompts)}: {prompt}")
        try:
            # Get response from the application
            response = get_answer(prompt)
            
            # Store the result
            results.append({
                "prompt": prompt,
                "response": response,
                "status": "Success"
            })
        except Exception as e:
            # Log any errors
            results.append({
                "prompt": prompt,
                "response": f"ERROR: {str(e)}",
                "status": "Error"
            })
            print(f"Error processing prompt: {str(e)}")
    
    # Save results to file
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"grocery_test_results_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Grocery Price Assistant Test Results\n")
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total prompts tested: {len(test_prompts)}\n")
        f.write(f"Success: {sum(1 for r in results if r['status'] == 'Success')}\n")
        f.write(f"Errors: {sum(1 for r in results if r['status'] == 'Error')}\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"Test #{i} - {result['status']}\n")
            f.write(f"Prompt: {result['prompt']}\n")
            f.write(f"Response:\n{result['response']}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"Test results saved to {filename}")
    return results

if __name__ == "__main__":
    run_tests()