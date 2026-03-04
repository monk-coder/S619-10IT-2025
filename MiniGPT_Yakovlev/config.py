import os

DATA_PATH = "data.txt"
TOKENIZER_PATH = "tokenizer.json"
NUM_MERGES = 1000
VAL_SPLIT = 0.1

GITHUB_DATA_URL = "https://github.com/monk-coder/S619-10IT-2025/blob/main/0/data.txt"

VOCAB_SIZE = None
D_MODEL = 128
N_HEAD = 4
N_LAYER = 3
D_FF = 512
MAX_SEQ_LEN = 128
DROPOUT = 0.1

BATCH_SIZE = 32
EPOCHS = 20
LR = 3e-4
BETA1 = 0.9
BETA2 = 0.999
EPS = 1e-8
GRAD_CLIP = 1.0

TEMPERATURE = 0.8
TOP_K = 50
MAX_NEW_TOKENS = 100

SEED = 42
SAVE_DIR = "checkpoints"
LOG_DIR = "logs"

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
