import secrets
import os

key = secrets.token_hex(64)
env_file = ".env"

# Content to write
content = f"SERVICE_API_KEY={key}\n"

# Check if .env exists to append or create
if os.path.exists(env_file):
    with open(env_file, "a") as f:
        f.write("\n" + content)
else:
    with open(env_file, "w") as f:
        f.write(content)

print(f"Generated Key: {key}")
