import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

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


async def load_source_text_async(file_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, load_source_text, file_path)


def build_ngrams(split_strategy: str, character_count: int) -> str:
    proc.stdin.write("build_ngrams\n")
    proc.stdin.flush()

    if split_strategy == "word":
        proc.stdin.write("word\n")  # TODO: implement dynamic size
    elif split_strategy == "character":
        proc.stdin.write(f'{character_count}\n')

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


async def build_ngrams_async(split_strategy: str, character_count: int) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, build_ngrams, split_strategy, character_count)


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


async def generate_text_async() -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, generate_text)
