import yaml
from pathlib import Path

_ROOT = Path(__file__).absolute().parent

from langfuse import Langfuse

langfuse = Langfuse(
  secret_key="sk-lf-34c5171f-370c-46b2-8325-2ef63c6844c4",
  public_key="pk-lf-246bf203-6214-4e3d-9d9b-14918c35f54e",
  host="https://cloud.langfuse.com"
)



def get_config(config: dict):
    # This loads things either ALL from configurable, or
    # all from the config.yaml
    # This is done intentionally to enforce an "all or nothing" configuration
    if "email" in config["configurable"]:
        return config["configurable"]
    else:
        with open(_ROOT.joinpath("config.yaml")) as stream:
            return yaml.safe_load(stream)
