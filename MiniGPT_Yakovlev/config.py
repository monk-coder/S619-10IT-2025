import os

DATA_PATH = "../0/data.txt"
TOKENIZER_PATH = "tokenizer.json"
NUM_MERGES = 500
VAL_SPLIT = 0.1

VOCAB_SIZE = None
D_MODEL = 64
N_HEAD = 2
N_LAYER = 2
D_FF = 128
MAX_SEQ_LEN = 64
DROPOUT = 0.1

BATCH_SIZE = 64
EPOCHS = 10
LR = 1e-3
BETA1 = 0.9
BETA2 = 0.999
EPS = 1e-8
GRAD_CLIP = 1.0

TEMPERATURE = 0.8
TOP_K = 50
MAX_NEW_TOKENS = 50

SEED = 42
SAVE_DIR = "checkpoints"
LOG_DIR = "logs"
VAL_SAMPLES = 20

USE_STREAMING = False
CHUNK_SIZE = 1000

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
