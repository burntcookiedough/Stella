
import ollama
import json

def analyze_health_data(user_summary: dict) -> str:
    """
    Sends the structured health summary to the local LLM (Mistral)
    and returns a concise, behavioral interpretation.
    """
    
    # 1. Construct the System Prompt (Guardrails)
    system_prompt = """
    You are an AI Health Assistant named Stella.
    Your goal is to interpret wearable data trends for a user.
    
    RULES:
    1. DO NOT provide medical diagnoses or advice.
    2. DO NOT mention specific diseases (e.g., "You might have diabetes").
    3. Focus on BEHAVIORAL insights (e.g., "Your sleep consistency has dropped").
    4. Be professionally encouraging but direct about negative trends.
    5. Keep the response under 150 words.
    6. Use bullet points for key insights.
    """

    # 2. Construct User Message
    user_prompt = f"""
    Here is the user's latest health data summary:
    {json.dumps(user_summary, indent=2)}
    
    Please analyze:
    - Sleep trends (Quantity and consistency)
    - Activity levels (Steps and intensity)
    - Overall health score
    - Any specific anomalies flagged
    
    Provide a "Status Update" and 2-3 specific "Actionable Tips".
    """

    try:
        # 3. Call Ollama
        response = ollama.chat(model='mistral:latest', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ])
        
        return response['message']['content']

    except Exception as e:
        return f"Error generating insight: {str(e)}. Ensure Ollama is running."
