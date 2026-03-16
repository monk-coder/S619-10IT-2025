"""Обучение модели с историей метрик"""
import numpy as np
from optimizers.sgd import SGD
from data.loader import one_hot

class Trainer:
    def __init__(self, model, optimizer, X_train, y_train, X_val, y_val, batch_size=64):
        self.model = model
        self.optimizer = optimizer
        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
        self.batch_size = batch_size
        
        self.history = {
            'train_loss': [], 'val_loss': [],
            'train_acc': [], 'val_acc': []
        }
    
    def train_epoch(self):
        indices = np.random.permutation(len(self.X_train))
        X_shuffled = self.X_train[indices]
        y_shuffled = self.y_train[indices]
        
        total_loss, correct = 0, 0
        
        for i in range(0, len(X_shuffled), self.batch_size):
            X_batch = X_shuffled[i:i+self.batch_size]
            y_batch = y_shuffled[i:i+self.batch_size]
            y_batch_one = one_hot(y_batch)
            
            # Forward
            y_pred = self.model.forward(X_batch)
            loss = self.model.loss(y_pred, y_batch_one)
            total_loss += loss * len(X_batch)
            correct += np.sum(np.argmax(y_pred, axis=1) == y_batch)
            
            # Backward + update
            self.model.backward(y_pred, y_batch_one)
            linear_layers = [l for l in self.model.layers if hasattr(l, 'W')]
            self.optimizer.step(linear_layers)
        
        return total_loss / len(X_shuffled), correct / len(X_shuffled)
    
    def validate(self):
        y_pred = self.model.forward(self.X_val)
        y_val_one = one_hot(self.y_val)
        loss = self.model.loss(y_pred, y_val_one)
        acc = np.mean(np.argmax(y_pred, axis=1) == self.y_val)
        return loss, acc
    
    def train(self, epochs):
        for epoch in range(epochs):
            train_loss, train_acc = self.train_epoch()
            val_loss, val_acc = self.validate()
            
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_acc'].append(val_acc)
            
            print(f"Epoch {epoch+1}/{epochs} | "
                  f"Train: loss={train_loss:.4f} acc={train_acc:.4f} | "
                  f"Val: loss={val_loss:.4f} acc={val_acc:.4f}")
        
        return self.history