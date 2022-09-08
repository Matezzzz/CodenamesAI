from common import *
import os
from colorama import Fore, Back, Style, init as colorama_init
colorama_init()




def colored(text, role, hidden = True):
    return f"{display_settings.roleColor(role, hidden)}{text}{Style.RESET_ALL}"



class ConsoleRenderer:
    @staticmethod
    def render(board, show_roles):
        for i, c in enumerate(board.cards):
            print(c.getStr(show_roles), end="")
            if (i + 1) % display_settings.width == 0:
                print()

    

if __name__ == '__main__':
    import main