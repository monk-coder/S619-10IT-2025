SPECIAL_TOKENS = {
    "<PAD>": 0,
    "<UNK>": 1,
    "<BOS>": 2,
    "<EOS>": 3
}

WORD_END_MARKER = "</w>"

DEFAULT_NUM_MERGES = 10000
DEFAULT_TRAIN_RATIO = 0.9

WORD_PATTERN = r"'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+"
