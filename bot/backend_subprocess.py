import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

executor = ThreadPoolExecutor()
proc_lock = threading.Lock()

# TODO: Change path
proc = subprocess.Popen(
    ['markov/markov'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1,
    encoding='utf-8'
)


def load_source_text(path: str) -> str:
    with proc_lock:
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
    with proc_lock:
        proc.stdin.write("build_ngrams\n")
        proc.stdin.flush()

        if split_strategy == "word":
            proc.stdin.write("word\n")
        elif split_strategy == "character":
            proc.stdin.write(f"{character_count}\n")
        else:
            raise ValueError(f"Invalid split strategy: {split_strategy}")
        proc.stdin.flush()

        # If updating ngrams
        if new_text:
            proc.stdin.write(new_text.strip() + "\n")
        proc.stdin.write("__END__INPUT__\n")
        proc.stdin.flush()

        # Collect output
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
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(executor, build_ngrams, split_strategy, character_count, new_text)
    except Exception as e:
        stderr = proc.stdout.read()
        print(f"[Subprocess Error] {e}\nStderr:\n{stderr}")
        raise


def generate_text(length_to_generate: int) -> str:
    with proc_lock:
        if proc.poll() is not None:
            raise RuntimeError("Backend process is not running.")

        try:
            proc.stdin.write("generate\n")
            proc.stdin.flush()
            proc.stdin.write(f"{length_to_generate}\n")
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


async def generate_text_async(length_to_generate: int) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, generate_text, length_to_generate)


def save_ngrams(path: str) -> str:
    with proc_lock:
        proc.stdin.write("save\n")
        proc.stdin.flush()
        proc.stdin.write(f"{path}\n")
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


async def save_ngrams_async(path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, save_ngrams, path)


def load_ngrams(path: str) -> str:
    with proc_lock:
        proc.stdin.write("load\n")
        proc.stdin.flush()
        proc.stdin.write(f"{path}\n")
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


async def load_ngrams_async(path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, load_ngrams, path)
