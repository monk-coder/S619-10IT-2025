import random
import json
import os
from money.balances import Balances


class Rulete:
    def __int__(self, bot):
        self.bot = bot
        self.red = "Красное"
        self.black = "Черное"
        self.green = "Зеленое"
        self.colors = [self.red, self.black, self.green]
        self.numbers = list(range(0, 37))
        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        self.green_numbers = [0]
        self.bets = {}

    def spin_wheel(self):
        number = random.choice(self.numbers)
        color = self.get_color_by_number(number)
        return number, color


    def get_color_by_number(self, colors, number):
        if number == self.green_numbers:
            return self.green
        elif number in self.red_numbers:
            return self.red
        else:
            return self.black


    def result
