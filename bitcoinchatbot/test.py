import requests
from datetime import datetime, timedelta

def get_news_previous_day(api_key, query='Bitcoin'):
    # Calculate the previous date
    previous_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    
    # Define the API endpoint and parameters
    api_url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'from': previous_date,
        'sortBy': 'popularity',
        'apiKey': api_key
    }
    
    # Send the GET request to the NewsAPI
    response = requests.get(api_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Extract just one article
        if data['status'] == 'ok' and len(data['articles']) > 0:
            article = data['articles'][0]  # Get the first article
            
            # Format the article details
            title = article.get('title', 'No title available')
            description = article.get('description', 'No description available')
            url = article.get('url', 'No URL available')
            
            # Format the message
            message = f"Title: {title}\nDescription: {description}\nRead more: {url}"
        else:
            message = "No articles found."
    else:
        message = f"Error: {response.status_code} - {response.reason}"
    
    return message

# Example usage
api_key = '9d1945a8c6df4ded9f10cf2bf6afb062'
news_message = get_news_previous_day(api_key)
print(news_message)  # This would be used in msg.body(news_message) in a chatbot context
