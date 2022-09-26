from common import *
import os
from colorama import Fore, Back, Style, init as colorama_init

#initialize colorama for colorful text in the console
colorama_init()



#print a text in the color of a given role. if hidden=False, color background as well
def colored(text, role, hidden = True):
    return f"{display_settings.roleColor(role, hidden)}{text}{Style.RESET_ALL}"


#print a board into a console
class ConsoleRenderer:
    #print given board, showing roles if instructed to do so
    @staticmethod
    def render(board, show_roles):
        for i, c in enumerate(board.cards):
            print(c.getStr(show_roles), end="")
            #one whole board line was printed - add enter
            if (i + 1) % display_settings.width == 0:
                print()

    

if __name__ == '__main__':
    import main