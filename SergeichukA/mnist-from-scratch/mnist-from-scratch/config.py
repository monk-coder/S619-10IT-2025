"""Гиперпараметры модели"""
import argparse

def get_config():
    parser = argparse.ArgumentParser(description='MNIST Classifier')
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.01)
    parser.add_argument('--hidden', type=int, nargs='+', default=[128, 64])
    parser.add_argument('--reg', type=float, default=0.001)
    parser.add_argument('--save_plots', action='store_true')
    return parser.parse_args()