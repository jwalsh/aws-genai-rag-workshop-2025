# src/examples/hello_world.py

def greet(name: str = "World") -> str:
    """Returns a greeting message."""
    message = f"Hello, {name}! Your Python environment is working."
    print(message)
    return message

if __name__ == "__main__":
    greet()
