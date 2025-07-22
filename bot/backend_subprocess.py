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
    pass
