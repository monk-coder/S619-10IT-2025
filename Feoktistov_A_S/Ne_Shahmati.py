from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QGridLayout, QProgressBar, QStylePainter
from symtable import Class
import time
import sys
from PySide6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel
from PySide6.QtCore import Qt
import random

doubleClick = False

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


class window(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 200, 200, 50)
        self.setWindowTitle("НЕ Шахматы")
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        button = QPushButton("ДЕПОРТИРОВАТЬ")
        button.setStyleSheet(f"""
                            background-color: red;
                            font-size: 10px;
                            font-weight: bold;
                            text-align: center;
                        """)
        button.setFixedSize(200, 50)
        button.clicked.connect(lambda: deportirovat(pieces, widgets))
        self.layout.addWidget(button, 0, 0)


def deportirovat(pieces, widgets):
    print("ДЕПОРТИРОВАН")
    r = random.randint(0, 64)
    print(r)
    print(pieces)
    piece = pieces[r // 8][r % 8]
    print(piece)
    if piece == "️👨🏿‍🦽" or piece == "🐎" or piece == "🚴🏿‍♂️" or piece == "🧕🏿" or piece == "🤴🏿" or piece == "👳🏿‍♂️":
        pieces[r // 8].pop(r % 8)
        pieces[r // 8].insert(r % 8, "")
    else:
        pass
    desk = Desk()
    return pieces, desk


def able_check(t, button,i,j):
    if t == 1:
        able = ["🚔", "🔫", "💂🏻‍♂️", "👩🏻‍🍳", "👨🏻‍⚖️", "👮🏻‍♂️", ""]
    else:
        able = ["👨🏿‍🦽", "🐎", "🚴🏿‍♂️", "🧕🏿", "🤴🏿", "", "👳🏿‍♂️"]
    check = False
    for g in range(7):
        if button.text() == able[g]:
            if i>=0 and j>=0:
                check = True
                print("успех")
            else:
                print("Выход за пределы поля")
    return check


class Pieces:
    def __init__(self, i, j, widgets):
        self.able = []

    def pawn(self, i, j, widgets):
        button = widgets[i][j]
        text = button.text()
        self.append(button)
        if text == "🐎" or text == "🚴🏿‍♂️" or text == "🧕🏿" or text == "🤴🏿" or text == "👳🏿‍♂️" or text == "👨🏿‍🦽":
            t = 1
        else:
            t = -1

        if t == 1:
            print("self.team = 1")
        else:
            print("self.team = -1")
        print(self,"able1")
        for l in range(3):
            button = widgets[i+t][j + l - 1]
            if l-1 == 0:
                if button.text() == "":
                    button.setStyleSheet("""background-color: orange;font-size: 40px;""")
                    self.append(button)
            else:
                if (button.text() == "🐎" or button.text() == "🚴🏿‍♂️" or button.text() == "🧕🏿" or button.text() == "🤴🏿" or button.text() == "👳🏿‍♂️" or
                    button.text() == "👨🏿‍🦽") and t == -1:
                    button.setStyleSheet("""background-color: red;font-size: 40px;""")
                    self.append(button)

                if (button.text() == "👮🏻‍♂️" or button.text() == "🚔" or button.text() == "👩🏻‍🍳" or button.text() == "👨🏻‍⚖️" or button.text() == "🔫" or
                    button.text() == "💂🏻‍♂️") and t == 1:
                    button.setStyleSheet("""background-color: red;font-size: 40px;""")
                    self.append(button)

    def horse(self,i, j, widgets):
        text = widgets[i][j].text()
        self.append(widgets[i][j])
        print("piece horse")
        if text == "🐎":
            t = 1
        else:
            t = -1
        positions = [[i+1,j+2],[i-1,j+2],[i-1,j-2],[i+1,j-2],[i+2,j-1],[i+2,j+1],[i-2,j+1],[i-2,j-1]]
        for k in range(8):
            i = positions[k][0]
            j = positions[k][1]
            if 0 <= i < 8 and 0 <= j < 8:
                print(i,j,"horse")
                print(i,j)
                button = widgets[i][j]
                check = able_check(t,button,i,j)
                if check == True:
                    button.setStyleSheet("""background-color: red;font-size: 40px;""")
                    self.append(button)

        print("horse", self)
        button = widgets[i][j]
        self.append(button)

    def queen(self, i, j, widgets):
        button = widgets[i][j]
        text = button.text()
        print("piece queen")
        if text == "🧕🏿":
            t = 1
        else:
            t = -1
        self.append(button)
        print(i, j, "queen")

        for k in range(1, 8):
            i0 = i - k
            if i0 < 0:
                break
            button = widgets[i0][j]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i + k
            if i0 >= 8:
                break
            button = widgets[i0][j]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            j0 = j - k
            if j0 < 0:
                break
            button = widgets[i][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break

        for k in range(1, 8):
            j0 = j + k
            if j0 >= 8:
                break
            button = widgets[i][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i - k
            j0 = j - k
            if i0 < 0 or j0 < 0:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i - k
            j0 = j + k
            if i0 < 0 or j0 >= 8:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i + k
            j0 = j - k
            if i0 >= 8 or j0 < 0:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i + k
            j0 = j + k
            if i0 >= 8 or j0 >= 8:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break

    def rook(self,i,j,widgets):
        button = widgets[i][j]
        self.append(button)
        button = widgets[i][j]
        if button.text() == "🚔":
            t = -1
        else:
            t = 1
        self.append(button)
        for k in range(1, 8):
            i0 = i - k
            if i0 < 0:
                break
            button = widgets[i0][j]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k1 in range(1, 8):
            i0 = i + k1
            if i0 >= 8:
                break
            button = widgets[i0][j]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k2 in range(1, 8):
            j0 = j + k2
            if j0 >= 8:
                break
            else:
                button = widgets[i][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k3 in range(1, 8):
            j0 = j - k3
            if j0 < 0:
                break
            button = widgets[i][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break

    def king(self,i,j,widgets):
        button = widgets[i][j]
        self.append(button)
        if button.text()== "🤴🏿":
            t = 1
        else:
            t = -1
        positions = [[i + 1, j + 1], [i + 1, j], [i + 1, j - 1], [i, j - 1], [i, j + 1], [i - 1, j + 1],
                     [i - 1, j - 1], [i - 1, j]]
        for k in range(8):
            i0 = positions[k][0]
            j0 = positions[k][1]
            if 8 > i0 >= 0 and 0 <= j0 < 8:
                print(i, j, "king")
                print(i, j)
                button = widgets[i0][j0]
                check = able_check(t, button, i0, j0)
                if check == True:
                    button.setStyleSheet("""background-color: red;font-size: 40px;""")
                    self.append(button)

    def piece_last(self,i,j,widgets):
        button = widgets[i][j]
        self.append(button)
        if button.text() == "🚴🏿‍♂️":
            t = 1
        else:
            t = -1
        for k in range(1, 8):
            i0 = i - k
            j0 = j - k
            if i0 < 0 or j0 < 0:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i - k
            j0 = j + k
            if i0 < 0 or j0 >= 8:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i + k
            j0 = j - k
            if i0 >= 8 or j0 < 0:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break
        for k in range(1, 8):
            i0 = i + k
            j0 = j + k
            if i0 >= 8 or j0 >= 8:
                break
            button = widgets[i0][j0]
            check = able_check(t, button, i, j)
            if check:
                button.setStyleSheet("background-color: red;font-size: 40px;")
                self.append(button)
            if button.text() != "":
                break


    def able_check(self,t,button):
        if t == 1:
            able = ["🚔", "🔫", "💂🏻‍♂️", "👩🏻‍🍳", "👨🏻‍⚖️","👮🏻‍♂️",""]
        else:
            able = ["👨🏿‍🦽", "🐎", "🚴🏿‍♂️", "🧕🏿", "🤴🏿","","👳🏿‍♂️"]
        for g in range(7):
            if button.text() == able[g]:
                check = True
        return check

class Desk(QWidget):
    print(doubleClick)

    def __init__(self):
        super().__init__()
        self.setGeometry(300, 200, 400, 400)
        self.setWindowTitle("НЕ Шахматы")
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        clicked = []
        widgets = [[],[],[],[],[],[],[],[]]
        able = []
        print(doubleClick)
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
                button.clicked.connect(lambda checked, i=i, j=j, widgets=widgets,
                                              button=button, able=able, pieces=pieces: self.movement(i, j, widgets,
                                                                                                     button, clicked,
                                                                                                     pieces, able))
                self.layout.addWidget(button, i, j)

    def movement(self, i, j, widgets, button, clicked, pieces, able):
        piece = str(widgets[i][j].text())
        print(piece, "movement")
        global doubleClick

        def reset():
            print("reset")
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

        def is_able(able, i, j, is_able):
            button = widgets[i][j]
            is_able_to = False
            for k in range(len(able)):
                if able[k] == button:
                    is_able_to = True
                else:
                    print("НЕТ")
            return is_able_to

        if doubleClick == False:
            if piece == "":
                print("пусто")
                pass
            else:
                doubleClick = True
                button = widgets[i][j]
                text = button.text()
                clicked.append(text)
                clicked.append([i, j])

                if text == "👳🏿‍♂️" or text == "👮🏻‍♂️":
                    Pieces.pawn(able,i, j, widgets)

                if text == "🐎" or text == "🔫":
                    Pieces.horse(able,i,j,widgets)

                if text == "🚔" or text == "👨🏿‍🦽":
                    Pieces.rook(able,i,j,widgets)

                if text == "🧕🏿" or text == "👩🏻‍🍳":
                    Pieces.queen(able,i,j,widgets)

                if text == "🤴🏿" or text == "👨🏻‍⚖️":
                    Pieces.king(able,i,j,widgets)

                if text == "🚴🏿‍♂️" or text == "💂🏻‍♂️":
                    Pieces.piece_last(able,i,j,widgets)

                button.setText("*")

                if text == "":
                    print("ergefd")

        else:
            is_able_to = is_able(able, i, j, is_able)
            if is_able_to == True:
                print("oeirthgp9eripug")
                print(clicked[0])
                i0 = clicked[1][0]
                j0 = clicked[1][1]
                button0 = widgets[i0][j0]
                button0.setText("")
                button = widgets[i][j]
                text2 = str(clicked[0])
                button.setText(text2)
                print(clicked)
                reset()
                clicked.clear()
                able.clear()
                doubleClick = False
                is_able = False
            else:
                print(i,j)
                print("2305738947934845769834765")


game = QApplication()
desk = Desk()
window = window()
desk.show()
sys.exit(game.exec())
