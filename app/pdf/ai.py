import requests

def ask_pollinations(prompts):
    """Menghubungi API Pollinations dengan prompt tertentu"""
    url = f"https://text.pollinations.ai/openai/{prompts}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"API Error: {e}"
