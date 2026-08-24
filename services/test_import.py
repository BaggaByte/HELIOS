import sys
import types

fake_mods = [
    "chromadb", "crewai", "langchain", "langchain.agents",
    "openvino", "openvino_genai", "optimum", "optimum.intel",
    "sentence_transformers", "transformers", "litellm",
    "yara", "lief", "celery", "jsbeautifier"
]
class MockModule(types.ModuleType):
    def __getattr__(self, name):
        return MockModule(f"{self.__name__}.{name}")

for name in fake_mods:
    sys.modules[name] = MockModule(name)
    # Also mock specific submodules that are imported directly
    sys.modules[f"{name}.config"] = MockModule(f"{name}.config")
    sys.modules[f"{name}.agents"] = MockModule(f"{name}.agents")
    sys.modules[f"{name}.intel"] = MockModule(f"{name}.intel")

# common attrs pulled at import time in various wrappers
sys.modules["chromadb"].PersistentClient = lambda *a, **k: None
sys.modules["sentence_transformers"].SentenceTransformer = object
sys.modules["openvino_genai"].LLMPipeline = object
sys.modules["celery"].Celery = object
sys.modules["yara"].compile = lambda *a, **k: object()

sys.path.insert(0, ".")
try:
    import helios.main  # noqa
    print("IMPORT OK — app object constructed without errors")
except Exception:
    import traceback
    traceback.print_exc()
