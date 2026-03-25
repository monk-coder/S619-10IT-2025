import numpy as np


class Config:
    """Configuration class for the transformer model"""

    def __init__(self):
        # Data
        self.data_path = "data.txt"
        self.train_split = 0.9

        # Model
        self.vocab_size = None  # Will be set after tokenization
        self.d_model = 128  # Embedding dimension
        self.n_head = 4  # Number of attention heads
        self.n_layer = 3  # Number of transformer blocks
        self.block_size = 128  # Context length (T)
        self.dropout = 0.1  # Dropout rate

        # Training
        self.batch_size = 32
        self.learning_rate = 0.01
        self.momentum = 0.9
        self.n_epochs = 50
        self.eval_interval = 5

        # Generation
        self.max_new_tokens = 100
        self.temperature = 0.8
        self.top_k = 40

        # Other
        self.seed = 42
        self.dtype = np.float32