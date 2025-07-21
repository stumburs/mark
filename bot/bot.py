import subprocess


def get_markov_response():
    try:
        result = subprocess.run(
            ["../markov/markov"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Error generating response."
    except Exception as e:
        return f"Exception: {e}"


if __name__ == "__main__":
    response = get_markov_response()
    print(response)