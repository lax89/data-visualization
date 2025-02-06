# Load model directly
from transformers import AutoModelForCausalLM, AutoTokenizer
# from transformers.pytorch_utils import is_torch_greater_or_equal_than_2_1
from transformers.pytorch_utils import is_torch_greater_or_equal_than_2_1
model = AutoModelForCausalLM.from_pretrained("deepseek-ai/DeepSeek-R1", trust_remote_code=True)
# Use a pipeline as a high-level helper

import torch

# # Load model and tokenizer
# model_name = "deepseek-ai/deepseek-llm-7b"  # Replace with the specific DeepSeek model you want
tokenizer = AutoTokenizer.from_pretrained(model)
model1 = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.float16, device_map="auto")

# # Move model to GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model1.to(device)
def generate_text(prompt, max_length=100):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model1.generate(**inputs, max_length=max_length)
    
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Example Usage
prompt = "What is the future of AI?"
response = generate_text(prompt)
# print(response)
