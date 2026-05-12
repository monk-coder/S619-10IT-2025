from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QGridLayout, QMessageBox
from PySide6.QtCore import Qt
import random
import sys

doubleClick = False
widgets = [[], [], [], [], [], [], [], []]
turn = True

pieces = [
    ["👨🏿‍🦽", "🐎", "🚴🏿‍♂️", "🧕🏿", "🤴🏿", "🚴🏿‍♂️", "🐎", "👨🏿‍🦽"],
    ["👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️", "👳🏿‍♂️"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️", "👮🏻‍♂️"],
    ["🚔", "🔫", "💂🏻‍♂️", "👩🏻‍🍳", "👨🏻‍⚖️", "💂🏻‍♂️", "🔫", "🚔"]
]


def able_check(t, button, i, j):
    if t == 1:
        able = ["🚔", "🔫", "💂🏻‍♂️", "👩🏻‍🍳", "👨🏻‍⚖️", "👮🏻‍♂️", ""]
    else:
        able = ["👨🏿‍🦽", "🐎", "🚴🏿‍♂️", "🧕🏿", "🤴🏿", "", "👳🏿‍♂️"]
    check = False
    for g in range(7):
        if button.text() == able[g]:
            if i >= 0 and j >= 0:
                check = True
                print("успех")
            else:
                print("Выход за пределы поля")
    return check


def deportirovat():
    global widgets
    print("ДЕПОРТИРОВАН")
    cicle = True
    n = 0
    while cicle == True:
        n = n + 1
        if n > 47:
            break
        else:
            r = random.randint(0, 7)
            col = random.randint(0, 7)
            print(r)
            button = widgets[r][col]
            print(button.text())
            if button.text() == "💂🏻‍♂️" or button.text() == "🚔" or button.text() == "🔫" or button.text() == "👩🏻‍🍳" or button.text() == "👮🏻‍♂️" or button.text() == "" or button.text() == "👨🏻‍⚖️" or button.text() == "🤴🏿":
                text = "Нет фигур для депортации"
                button_text = "-"
            else:
                text = "Фигура депортирована"
                cicle = False
                button_text = button.text()
                button.setText("")

    msg_box = QMessageBox()
    msg_box.setWindowTitle("⚠️ ДЕПОРТАЦИЯ")
    msg_box.setText(f"{text} {button_text}")
    msg_box.exec()

class Piece:
    def __init__(self, i, j, widgets):
        self.i = i
        self.j = j
        self.widgets = widgets
        self.able = []

    def get_able_moves(self):
        return self.able

    def is_able(self):
        for button in self.able:
            button.setStyleSheet("background-color: red;font-size: 40px;")

    def reset(self):
        for i in range(8):
            for j in range(8):
                button = self.widgets[i][j]
                if (i + j) % 2 == 0:
                    color = "#F0D9B5"
                else:
                    color = "#B58863"
                button.setStyleSheet(f"""
                    background-color: {color};
                    font-size: 40px;
                    font-weight: bold;
                    text-align: center;
                """)


class Pawn(Piece):
    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()

    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()

        if text == "👳🏿‍♂️":
            t = 1
        else:
            t = -1

        self.able.append(button)
        if 0 <= self.i + t < 8:
            if self.widgets[self.i + t][self.j].text() == "":
                self.able.append(self.widgets[self.i + t][self.j])

        if (t == 1 and self.i == 1) or (t == -1 and self.i == 6):
            if 0 <= self.i + 2 * t < 8:
                if self.widgets[self.i + t][self.j].text() == "" and self.widgets[self.i + 2 * t][self.j].text() == "":
                    button = self.widgets[self.i + 2 * t][self.j]
                    self.able.append(button)
                    button.setStyleSheet(f"""
                            background-color: orange;
                            font-size: 10px;
                            font-weight: bold;
                            text-align: center;""")

        for l in [-1, 1]:
            if 0 <= self.i + t < 8 and 0 <= self.j + l < 8:
                target = self.widgets[self.i + t][self.j + l]
                if target.text() != "":
                    check = able_check(t, target, self.i + t, self.j + l)
                    if check:
                        self.able.append(target)

        if 0 <= self.i + t < 8:
            if self.widgets[self.i + t][self.j].text() == "":
                self.able.append(self.widgets[self.i + t][self.j])


class Knight(Piece):
    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()

    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()

        if text == "🐎":
            t = 1
        else:
            t = -1
        self.able.append(button)
        positions = [[self.i + 1, self.j + 2], [self.i - 1, self.j + 2], [self.i - 1, self.j - 2],
                     [self.i + 1, self.j - 2],
                     [self.i + 2, self.j - 1], [self.i + 2, self.j + 1], [self.i - 2, self.j + 1],
                     [self.i - 2, self.j - 1]]

        for pos in positions:
            i0 = pos[0]
            j0 = pos[1]
            if 0 <= i0 < 8 and 0 <= j0 < 8:
                button_target = self.widgets[i0][j0]
                check = able_check(t, button_target, i0, j0)
                if check:
                    self.able.append(button_target)


class Rook(Piece):
    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()


    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()

        if text == "🚔":
            t = -1
        else:
            t = 1
        self.able.append(button)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for di, dj in directions:
            for step in range(1, 8):
                i0 = self.i + di * step
                j0 = self.j + dj * step
                if not (0 <= i0 < 8 and 0 <= j0 < 8):
                    break

                button_target = self.widgets[i0][j0]
                check = able_check(t, button_target, i0, j0)
                if check:
                    self.able.append(button_target)

                if button_target.text() != "":
                    break

class Bishop(Piece):
    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()


    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()
        self.able.append(button)
        if text == "🚴🏿‍♂️":
            t = 1
        else:
            t = -1
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for di, dj in directions:
            for step in range(1, 8):
                i0 = self.i + di * step
                j0 = self.j + dj * step
                if not (0 <= i0 < 8 and 0 <= j0 < 8):
                    break
                button_target = self.widgets[i0][j0]
                check = able_check(t, button_target, i0, j0)
                if check:
                    self.able.append(button_target)
                if button_target.text() != "":
                    break


class Queen(Piece):

    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()

    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()

        if text == "🧕🏿":
            t = 1
        else:
            t = -1
        self.able.append(button)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        for di, dj in directions:
            for step in range(1, 8):
                i0 = self.i + di * step
                j0 = self.j + dj * step
                if not (0 <= i0 < 8 and 0 <= j0 < 8):
                    break

                button_target = self.widgets[i0][j0]
                check = able_check(t, button_target, i0, j0)
                if check:
                    self.able.append(button_target)

                if button_target.text() != "":
                    break


class King(Piece):
    def __init__(self, i, j, widgets):
        super().__init__(i, j, widgets)
        self.able_moves()

    def able_moves(self):
        self.able = []
        button = self.widgets[self.i][self.j]
        text = button.text()

        if text == "🤴🏿":
            t = 1
        else:
            t = -1

        positions = [[self.i + 1, self.j + 1], [self.i + 1, self.j], [self.i + 1, self.j - 1], [self.i, self.j - 1],
                     [self.i, self.j + 1], [self.i - 1, self.j + 1], [self.i - 1, self.j - 1], [self.i - 1, self.j]]
        self.able.append(button)
        for pos in positions:
            i0 = pos[0]
            j0 = pos[1]
            if 0 <= i0 < 8 and 0 <= j0 < 8:
                button_target = self.widgets[i0][j0]
                check = able_check(t, button_target, i0, j0)
                if check:
                    self.able.append(button_target)


class window(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(600, 200, 200, 50)
        self.setWindowTitle("НЕ Шахматы")
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setLayout(self.layout)
        button = QPushButton("ДЕПОРТИРОВАТЬ")
        button.setStyleSheet("""
                            background-color: red;
                            font-size: 10px;
                            font-weight: bold;
                            text-align: center;
                        """)
        button.setFixedSize(200, 50)
        button.clicked.connect(deportirovat)
        self.layout.addWidget(button, 0, 0)


class Desk(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 200, 400, 400)
        self.setWindowTitle("НЕ Шахматы")
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.clicked = []
        self.piece = None
        self.clicked_position = None

        for i in range(8):
            for j in range(8):
                piece = str(pieces[i][j])
                if (i + j) % 2 == 0:
                    color = "#F0D9B5"
                else:
                    color = "#B58863"
                button = QPushButton(piece)
                button.setStyleSheet(f"""
                    background-color: {color};
                    font-size: 40px;
                    font-weight: bold;
                    text-align: center;
                """)
                button.setFixedSize(50, 50)
                widgets[i].append(button)
                button.clicked.connect(lambda checked, i=i, j=j: self.movement(i, j))
                self.layout.addWidget(button, i, j)

    def reset(self):
        for i in range(8):
            for j in range(8):
                button = widgets[i][j]
                if (i + j) % 2 == 0:
                    color = "#F0D9B5"
                else:
                    color = "#B58863"
                button.setStyleSheet(f"""
                    background-color: {color};
                    font-size: 40px;
                    font-weight: bold;
                    text-align: center;
                """)
                button.setFixedSize(50, 50)

    def is_able(self, i, j):
        if self.piece:
            button = widgets[i][j]
            for able_button in self.piece.get_able_moves():
                if able_button == button:
                    return True
        return False

    def movement(self, i, j):
        global doubleClick, turn

        piece = str(widgets[i][j].text())
        white = ["🚔", "🔫", "💂🏻‍♂️", "👩🏻‍🍳", "👨🏻‍⚖️", "👮🏻‍♂️"]
        black = ["👨🏿‍🦽", "🐎", "🚴🏿‍♂️", "🧕🏿", "🤴🏿", "👳🏿‍♂️"]

        if doubleClick == False:
            if piece == "":
                pass
            else:
                if (turn == True and piece in white) or (turn == False and piece in black):
                    self.clicked = [piece, [i, j]]

                    if piece == "👳🏿‍♂️" or piece == "👮🏻‍♂️":
                        self.piece = Pawn(i, j, widgets)
                    if piece == "🐎" or piece == "🔫":
                        self.piece = Knight(i, j, widgets)
                    if piece == "🚔" or piece == "👨🏿‍🦽":
                        self.piece = Rook(i, j, widgets)
                    if piece == "🧕🏿" or piece == "👩🏻‍🍳":
                        self.piece = Queen(i, j, widgets)
                    if piece == "🤴🏿" or piece == "👨🏻‍⚖️":
                        self.piece = King(i, j, widgets)
                    if piece == "🚴🏿‍♂️" or piece == "💂🏻‍♂️":
                        self.piece = Bishop(i, j, widgets)

                    self.piece.is_able()
                    widgets[i][j].setText("*")
                    doubleClick = True
                else:
                    print("Чужой ход")
        else:
            if self.is_able(i, j):
                i0 = self.clicked[1][0]
                j0 = self.clicked[1][1]

                if i0 == i and j0 == j:
                    widgets[i0][j0].setText(str(self.clicked[0]))
                    doubleClick = False
                    self.piece.reset()
                    self.reset()
                    self.clicked.clear()
                    self.piece = None
                else:
                    widgets[i0][j0].setText("")
                    button = widgets[i][j]
                    text2 = str(self.clicked[0])

                    if button.text() == "🤴🏿" or button.text() == "👨🏻‍⚖️":
                        print("GAME OVER.")
                        if button.text() == "👨🏻‍⚖️":
                            t = "NIGGERS"
                        else:
                            t = "GOOD GUYS"
                        msg_box = QMessageBox()
                        msg_box.setWindowTitle("SYSTEM")
                        msg_box.setText(f"GAME OVER. TEAM {t} WON")
                        msg_box.exec()

                    turn = not turn
                    button.setText(text2)
                    self.piece.reset()
                    self.reset()
                    self.clicked.clear()
                    self.piece = None
                    doubleClick = False


game = QApplication()
desk = Desk()
desk.show()
window = window()
window.show()
sys.exit(game.exec())
