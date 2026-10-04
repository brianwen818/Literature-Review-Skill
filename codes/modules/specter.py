"""Optional SPECTER signal: environment check and embedding with a cache.

SPECTER needs torch and sentence-transformers (requirements-specter.txt).
Nothing here is imported unless the user turns the signal on."""
import os
import shutil
import subprocess
from importlib import util as importlib_util
from pathlib import Path

import numpy as np

MODEL_ID = "sentence-transformers/allenai-specter"
BATCH_SIZE = 32
WINDOW_CHARS = 1500      # a little under the model's 512-token limit
MAX_WINDOWS = 60
SEED_TOP_K = 5
# Encoding speed in title+abstract per second, used only for the time estimate.
# cpu is what the prototype measured (46,171 articles in 45 minutes); the GPU
# figures are rough assumptions, not measurements.
SPEED = {"cuda": 150.0, "mps": 40.0, "cpu": 17.0}


def model_cache_path():
    """Folder of an already-downloaded copy of the model, or None."""
    candidates = []
    hub = os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hub:
        candidates.append(Path(hub))
    home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    candidates.append(home / "hub")
    for base in candidates:
        for name in ("models--sentence-transformers--allenai-specter", "models--allenai--specter"):
            snapshots = base / name / "snapshots"
            if snapshots.is_dir() and any(snapshots.iterdir()):
                return base / name
    legacy = Path(os.environ.get("SENTENCE_TRANSFORMERS_HOME",
                                 Path.home() / ".cache" / "torch" / "sentence_transformers"))
    for name in ("sentence-transformers_allenai-specter", "allenai_specter"):
        if (legacy / name).is_dir():
            return legacy / name
    return None


def nvidia_gpu_name():
    """GPU reported by nvidia-smi (works without torch), or ''."""
    if not shutil.which("nvidia-smi"):
        return ""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=20)
        return out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout.strip() else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def check(n_texts=0):
    """Describe this machine and recommend whether to turn SPECTER on."""
    info = {
        "torch_installed": importlib_util.find_spec("torch") is not None,
        "sentence_transformers_installed": importlib_util.find_spec("sentence_transformers") is not None,
        "nvidia_gpu": nvidia_gpu_name(),
        "device": "cpu",
        "model_cached": False, "model_cache_path": "",
    }
    cache = model_cache_path()
    if cache:
        info["model_cached"], info["model_cache_path"] = True, str(cache)
    if info["torch_installed"]:
        import torch
        if torch.cuda.is_available():
            info["device"] = "cuda"
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            info["device"] = "mps"
        info["torch_version"] = torch.__version__
    ready = info["torch_installed"] and info["sentence_transformers_installed"]
    info["ready"] = ready
    expected_device = info["device"] if info["torch_installed"] else ("cuda" if info["nvidia_gpu"] else "cpu")
    if n_texts:
        info["estimated_minutes"] = round(n_texts / SPEED[expected_device] / 60, 1)
    steps = []
    if not ready:
        steps.append("pip install -r requirements-specter.txt")
    if info["nvidia_gpu"] and info["torch_installed"] and info["device"] != "cuda":
        steps.append("installed torch is CPU-only; install a CUDA build from https://pytorch.org to use the GPU")
    if info["nvidia_gpu"] and not info["torch_installed"]:
        steps.append("install a CUDA build of torch (https://pytorch.org) so the GPU is used")
    if not info["model_cached"]:
        steps.append("the model (about 440 MB) will be downloaded on first use")
    info["setup_steps"] = steps
    if expected_device in ("cuda", "mps"):
        info["recommendation"] = "on"
        info["reason"] = "a GPU is available, so the extra signal is cheap"
    elif n_texts and info.get("estimated_minutes", 0) <= 15:
        info["recommendation"] = "on"
        info["reason"] = "no GPU, but the candidate set is small enough for CPU"
    else:
        info["recommendation"] = "off"
        info["reason"] = "no GPU: CPU encoding is slow and the agent's reading covers the same ground"
    return info


def resolve_setting(setting, n_texts):
    """Config value (off | on | auto) -> (use_specter, info)."""
    setting = str(setting).lower()
    if setting in ("off", "false", "no", "0"):
        return False, {}
    info = check(n_texts)
    if setting in ("on", "true", "yes", "1"):
        if not info["ready"]:
            raise SystemExit("use_specter is 'on' but torch / sentence-transformers are missing.\n"
                             "  -> pip install -r requirements-specter.txt   (or set use_specter: off)")
        return True, info
    return info["ready"] and info["recommendation"] == "on", info


def windows(text):
    """Cut a long document into evenly spread windows the model can read."""
    text = " ".join((text or "").split())
    if len(text) <= WINDOW_CHARS:
        return [text] if text else []
    starts = list(range(0, len(text), WINDOW_CHARS))
    if len(starts) > MAX_WINDOWS:
        picks = np.linspace(0, len(starts) - 1, MAX_WINDOWS).round().astype(int)
        starts = [starts[i] for i in picks]
    return [text[s:s + WINDOW_CHARS] for s in starts]


class Encoder:
    def __init__(self, cache_file):
        from sentence_transformers import SentenceTransformer
        import torch

        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            device = "mps"
        self.model = SentenceTransformer(MODEL_ID, device=device)
        self.device = device
        self.sep = self.model.tokenizer.sep_token or "[SEP]"
        self.cache_file = Path(cache_file)
        self.cache = {}
        if self.cache_file.exists():
            stored = np.load(self.cache_file, allow_pickle=False)
            self.cache = dict(zip(stored["keys"].tolist(), stored["vectors"]))

    def paper(self, title, abstract):
        return f"{title or ''}{self.sep}{abstract or ''}"

    def encode(self, texts):
        return self.model.encode(list(texts), batch_size=BATCH_SIZE, normalize_embeddings=True,
                                 show_progress_bar=len(texts) > 200, convert_to_numpy=True)

    def encode_cached(self, keys, texts):
        """Embeddings for keyed texts; only keys not in the cache are encoded."""
        missing = [(k, t) for k, t in zip(keys, texts) if k not in self.cache]
        if missing:
            vectors = self.encode([t for _, t in missing])
            for (key, _), vector in zip(missing, vectors):
                self.cache[key] = vector
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            all_keys = list(self.cache)
            np.savez_compressed(self.cache_file, keys=np.array(all_keys),
                                vectors=np.vstack([self.cache[k] for k in all_keys]))
        return np.vstack([self.cache[k] for k in keys])


def specter_scores(frame, main_docs, seed_data, cache_file):
    """specter = mean of (best similarity to any main-document window,
    mean of the top-5 seed similarities), using whichever parts exist."""
    encoder = Encoder(cache_file)
    papers = encoder.encode_cached(
        frame["doi"].tolist(),
        [encoder.paper(t, a) for t, a in zip(frame["title"].fillna(""), frame["abstract"].fillna(""))])
    parts = []
    doc_windows = [w for _, text in main_docs for w in windows(text)]
    if doc_windows:
        parts.append((papers @ encoder.encode(doc_windows).T).max(axis=1))
    seeds = [encoder.paper(d["title"], d.get("abstract", "")) for d in seed_data.values() if d.get("title")]
    if seeds:
        sims = np.sort(papers @ encoder.encode(seeds).T, axis=1)[:, ::-1]
        parts.append(sims[:, :min(SEED_TOP_K, sims.shape[1])].mean(axis=1))
    if not parts:
        return np.full(len(frame), np.nan), encoder.device
    return np.mean(parts, axis=0), encoder.device
