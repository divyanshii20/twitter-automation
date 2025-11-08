import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --- Load the model and tokenizer once when the script starts ---
# UPDATED: Path now points to your 'deberta_model' folder
MODEL_PATH = r"C:\Users\Divyanshi\Downloads\tweeet_poster\deberta_model" 
print(f"Loading model from: {MODEL_PATH}")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

    # Check if a GPU is available and move the model to the GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Model loaded successfully on device: {device}")

except Exception as e:
    print(f"❌ ERROR: Could not load the model from '{MODEL_PATH}'.")
    print(f"Please make sure the folder exists and contains all necessary files (config.json, model.safetensors, etc.).")
    print(f"Details: {e}")
    exit()


def score_tweet(tweet_text: str) -> int:
    """
    Takes a raw tweet text and returns a score from 1-10 using the fine-tuned model.
    """
    if not tweet_text:
        return 0

    # 1. Tokenize the input text
    inputs = tokenizer(tweet_text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    
    # 2. Move tokenized inputs to the same device as the model (GPU or CPU)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # 3. Get predictions from the model
    with torch.no_grad(): # Disables gradient calculation for faster inference
        logits = model(**inputs).logits
    
    # 4. Find the label with the highest score using argmax.
    predicted_class_id = torch.argmax(logits, dim=1).item()
    
    # 5. Convert the 0-9 label back to a 1-10 score and return it.
    final_score = predicted_class_id + 1
    
    return final_score

# --- Example of how to use the function ---

   