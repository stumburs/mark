import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()
lock = asyncio.Lock()

# TODO: Change path
proc = subprocess.Popen(
    ['markov/markov'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
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


def build_ngrams(split_strategy: str, character_count: int, new_text: str | None = None) -> str:
    proc.stdin.write("build_ngrams\n")
    proc.stdin.flush()

    if split_strategy == "word":
        print("building with word")
        proc.stdin.write("word\n")
    elif split_strategy == "character":
        print("building with character", character_count)
        proc.stdin.write(f'{character_count}\n')
    else:
        raise ValueError(f'Invalid split strategy: {split_strategy}')

    proc.stdin.flush()

    if new_text:
        print("new text:", new_text)
        proc.stdin.write(new_text.strip() + "\n")
    proc.stdin.write("__END__INPUT__\n")
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


async def build_ngrams_async(split_strategy: str, character_count: int, new_text: str | None = None) -> str:
    if proc.poll() is not None:
        raise RuntimeError(
            "Backend process is not running (it may have crashed or exited)")
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(executor, build_ngrams, split_strategy, character_count, new_text)
    except Exception as e:
        stderr = proc.stdout.read()
        print(f"[Subprocess Error] {e}\nStderr:\n{stderr}")
        raise


def generate_text() -> str:
    if proc.poll() is not None:
        raise RuntimeError("Backend process is not running.")

    try:
        proc.stdin.write("generate\n")
        proc.stdin.flush()
        proc.stdin.write("100\n")
        proc.stdin.flush()
    except BrokenPipeError:
        print("BrokenPipeError: Subprocess pipe is closed.")
        stderr = proc.stdout.read()
        print("Subprocess stderr output:\n", stderr)
        raise

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
    async with lock:
        return await loop.run_in_executor(executor, generate_text)
