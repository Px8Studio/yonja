import ollama
import os

def import_gguf(model_name, gguf_path, system_prompt="You are a helpful assistant."):
    # Get absolute path for Windows compatibility
    abs_path = os.path.abspath(gguf_path)
    
    # Define the Modelfile logic dynamically
    modelfile = f"""
    FROM {abs_path}
    SYSTEM "{system_prompt}"
    PARAMETER temperature 0.7
    """
    
    print(f"📦 Importing {model_name} from {abs_path}...")
    ollama.create(model=model_name, modelfile=modelfile)
    print(f"✅ Model '{model_name}' is ready!")

if __name__ == "__main__":
    # Example usage:
    import_gguf("atllama", "models/atllama.v3.5.Q4_K_M.gguf")