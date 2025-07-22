import subprocess

# TODO: Change path
proc = subprocess.Popen(
    ['markov/markov'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)


def load_source_text(path: str) -> str:
    proc.stdin.write("load_source\n")
    proc.stdin.flush()
    proc.stdin.write(path + '\n')
    proc.stdin.flush()
    return proc.stdout.readline().strip()


# experimental
def build_ngrams() -> str:
    proc.stdin.write("build_ngrams\n")
    proc.stdin.flush()
    proc.stdin.write("word\n")
    proc.stdin.flush()
    return proc.stdout.readline().strip()


def generate_text() -> str:
    proc.stdin.write("generate\n")
    proc.stdin.flush()
    proc.stdin.write("100\n")
    proc.stdin.flush()

    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        if line == "__END__":
            break
        lines.append(line)

    return "\n".join(lines)
