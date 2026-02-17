
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

def chat_with_stella(context: dict, user_message: str):
    """
    Handles interactive chat with Stella, using the user's health context.
    Returns a generator that yields chunks of the response.
    """
    system_prompt = f"""
    You are Stella, an AI Health Assistant.
    Answer the user's question based on their health data context below.
    
    USER CONTEXT:
    {json.dumps(context, indent=2)}
    
    RULES:
    1. Be concise (under 3 sentences unless asked for detail).
    2. Use a friendly, professional tone.
    3. Refer to specific metrics in the context if relevant.
    4. If the user asks about something not in the data, say you don't know but offer general advice.
    5. NO MEDICAL DIAGNOSIS.
    """

    try:
        stream = ollama.chat(
            model='mistral:latest', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            stream=True
        )
        
        for chunk in stream:
            yield chunk['message']['content']
            
    except Exception as e:
        yield f"I'm having trouble thinking right now. (Error: {str(e)})"
