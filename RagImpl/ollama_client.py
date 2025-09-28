import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

def ask_ollama(prompt: str) -> str:
    """
    Send a prompt to Ollama via REST API and return the response.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": MODEL_NAME, "prompt": prompt},
            stream=True
        )

        if response.status_code != 200:
            return f"⚠️ Ollama API error: {response.status_code} - {response.text}"

        final_output = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    final_output += data["response"]
                if data.get("done", False):
                    break

        return final_output.strip() if final_output else "⚠️ No response from Ollama."

    except Exception as e:
        return f"⚠️ Error connecting to Ollama: {e}"


if __name__ == "__main__":
    q = "Explain Retrieval-Augmented Generation in simple terms."
    print("Sending test query to Ollama...")
    print(ask_ollama(q))
