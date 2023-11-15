import subprocess
import time


def start_bot():
    while True:
        try:
            subprocess.run(["python3.10", "splitbot.py"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(5)  # Wait before restarting


if __name__ == "__main__":
    start_bot()
