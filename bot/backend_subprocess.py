import subprocess

proc = subprocess.Popen(
    ['../markov/markov'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)


if __name__ == "__main__":
    print(proc.stdout.readline())

    try:
        while True:
            user_input = input(">>> ")
            if not user_input.strip():
                continue

            proc.stdin.write(user_input + '\n')
            proc.stdin.flush()

            response = proc.stdout.readline().strip()
            print(response)

            if user_input.strip == "exit":
                break

    except KeyboardInterrupt:
        print("\n[Interrupted] Exiting...")

    finally:
        proc.terminate()
        proc.wait()
