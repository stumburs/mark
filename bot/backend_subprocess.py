import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import markov

executor = ThreadPoolExecutor()


class BackendBase:
    async def load_source_text(self, path: str) -> str:
        raise NotImplementedError

    async def build_ngrams(self, split_strategy: str, character_count: int, new_text: str | None = None) -> str:
        raise NotImplementedError

    async def generate_text(self, length_to_generate: int) -> str:
        raise NotImplementedError

    async def save_ngrams(self, path: str) -> str:
        raise NotImplementedError

    async def load_ngrams(self, path: str) -> str:
        raise NotImplementedError


class PyBackend(BackendBase):
    async def load_ngrams(self, path: str) -> str:
        return await markov.load_ngrams_from_binary(path=path)

    async def save_ngrams(self, path: str) -> str:
        return await markov.save_ngrams_to_binary(path=path)

    async def generate_text(self, length_to_generate: int) -> str:
        return await markov.generate_text(length=length_to_generate)

    async def build_ngrams(self, split_strategy: str, character_count: int, new_text: str | None) -> str:
        return await markov.build_ngrams(split_strategy=split_strategy, character_count=character_count, optional_text=new_text)


# NOTE:
# CPP backend is deprecated
class CppBackend(BackendBase):
    def __init__(self, path: str = "markov/markov"):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )
        self.proc_lock = threading.Lock()

    async def load_source_text(self, path: str) -> str:
        def _load():
            with self.proc_lock:
                self.proc.stdin.write("load_source\n")
                self.proc.stdin.flush()

                self.proc.stdin.write(path + '\n')
                self.proc.stdin.flush()

                lines = []
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break

                    line = line.strip()
                    if line == "__END__":
                        break
                    lines.append(line)

                return "\n".join(lines)

        return await asyncio.get_event_loop().run_in_executor(executor=executor, func=_load)

    async def build_ngrams(self, split_strategy: str, character_count: int, new_text: str | None) -> str:
        def _build_ngrams():
            with self.proc_lock:
                self.proc.stdin.write("build_ngrams\n")
                self.proc.stdin.flush()

                if split_strategy == "word":
                    self.proc.stdin.write("word\n")
                elif split_strategy == "character":
                    self.proc.stdin.write(f"{character_count}\n")
                else:
                    raise ValueError(
                        f"Invalid split strategy: {split_strategy}")
                self.proc.stdin.flush()

                # If updating ngrams
                if new_text:
                    self.proc.stdin.write(new_text.strip() + "\n")
                self.proc.stdin.write("__END__INPUT__\n")
                self.proc.stdin.flush()

                # Collect output
                lines = []
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line == "__END__":
                        break
                    lines.append(line)

                return "\n".join(lines)

        try:
            return await asyncio.get_event_loop().run_in_executor(executor, _build_ngrams)
        except Exception as e:
            stderr = self.proc.stdout.read()
            print(f"[Subprocess Error] {e}\nStderr:\n{stderr}")
            raise

    async def generate_text(self, length_to_generate: int) -> str:
        def _generate_text():
            with self.proc_lock:
                if self.proc.poll() is not None:
                    raise RuntimeError("Backend process is not running.")

                try:
                    self.proc.stdin.write("generate\n")
                    self.proc.stdin.flush()
                    self.proc.stdin.write(f"{length_to_generate}\n")
                    self.proc.stdin.flush()
                except BrokenPipeError:
                    print("BrokenPipeError: Subprocess pipe is closed.")
                    stderr = self.proc.stdout.read()
                    print("Subprocess stderr output:\n", stderr)
                    raise

                lines = []
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line == "__END__":
                        break
                    lines.append(line)

                return "\n".join(lines)

        return await asyncio.get_running_loop().run_in_executor(executor, _generate_text)

    async def save_ngrams(self, path: str) -> str:
        def _save_ngrams():
            with self.proc_lock:
                self.proc.stdin.write("save\n")
                self.proc.stdin.flush()
                self.proc.stdin.write(f"{path}\n")
                self.proc.stdin.flush()

                lines = []
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line == "__END__":
                        break
                    lines.append(line)

                return "\n".join(lines)

        return await asyncio.get_running_loop().run_in_executor(executor, _save_ngrams)

    async def load_ngrams(self, path: str) -> str:
        def _load_ngrams():
            with self.proc_lock:
                self.proc.stdin.write("load\n")
                self.proc.stdin.flush()
                self.proc.stdin.write(f"{path}\n")
                self.proc.stdin.flush()

                lines = []
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line == "__END__":
                        break
                    lines.append(line)

                return "\n".join(lines)

        return await asyncio.get_running_loop().run_in_executor(executor, _load_ngrams)
