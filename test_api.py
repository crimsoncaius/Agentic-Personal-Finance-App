# test_api.py
import requests

def test_categories_api():
    try:
        # Send a GET request to the categories endpoint
        response = requests.get('http://localhost:8000/categories/')
        
        # Print the response status code
        print(f"Status Code: {response.status_code}")
        
        # Print the response headers
        print("\nHeaders:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        # Print the response body
        print("\nResponse Body:")
        if response.status_code == 200:
            categories = response.json()
            if categories:
                print(f"Found {len(categories)} categories:")
                for category in categories:
                    print(f"  - ID: {category['id']}, Name: {category['name']}, Type: {category['transaction_type']}")
            else:
                print("No categories found.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_categories_api() 