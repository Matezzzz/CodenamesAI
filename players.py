from multiprocessing.sharedctypes import Value
from common import *

from board import Board
from model import AgentModel, CaptainModel, Hint
from renderer import ConsoleRenderer, colored, clear



class CaptainPlayer:
    team : int = UNKNOWN
    
    def playTurn(self, board : Board, team : int):
        print (f"Current turn: {colored('Captain', team)}")
        hint = self.giveHint(board, team)
        board.disableHint(hint.word_i)
        print (f"Given hint: {hint.colored(team)}")
        press_enter_clear()
        return hint
            
    def giveHint(self, board : Board, team : int):
        return Hint.Invalid()
    

class AICaptainPlayer(CaptainPlayer):
    model : CaptainModel
    
    def __init__(self, model):
        self.model = model
    
    def giveHint(self, board : Board, team : int) -> Hint:
        return self.model.giveHint(team, board)
    

class HumanCaptainPlayer(CaptainPlayer):
    def giveHint(self, board : Board, team : int) -> Hint:
        input("Press ENTER to show the board, with colored roles")
        print (f"Current board:")
        ConsoleRenderer.render(board, True)
        while True:
            hint = input ("The hint to give: ")
            hint_i = dictionary.hintWordI(hint)
            if hint_i != -1:
                break
            else:
                print ("This word isn't in the dictionary - AI models cannot guess based on it, try another one. Sorry :(")
        
        while True:
            try:
                count = int(input ("How many words are related to this hint: "))
                break
            except ValueError:
                print ("Given value must be an integer. Try again.")
        return Hint(hint_i, count)




class AgentPlayer:
    def playTurn(self, board : Board, hint : Hint, team : int):
        print (f"Current turn: {colored('Agent', team)}")
        self.guess(board, hint, team)
        print ("Board after turn:")
        ConsoleRenderer.render(board, False)
        press_enter_clear()
    
    def guess(self, board : Board, hint : Hint, team : int):
        for rem_hints in range(hint.count + 1, -1, -1):
            print (f"Given hint: {hint.colored(team)}, Remaining guesses: {rem_hints - 1} + {1}")
            card_i = self.guessWord(board, hint, rem_hints)
            if card_i == None: break
            role = board.guess(card_i)
            word = role.getStr(True)
            if role.role != team:
                print (f"Guessed a wrong word ({word}). Your turn ends.")
                break
            else:
                print (f"Guessed correctly ({word})")
            if board.game_ended: break
    
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        return None
        
    
    
class AIAgentPlayer(AgentPlayer):
    model : AgentModel
    
    def __init__(self, model):
        self.model = model
    
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        return self.model.guess(board, hint)
    


class HumanAgentPlayer(AgentPlayer):
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        print("Current board:")
        ConsoleRenderer.render(board, False)
        guess = input("Guess(Nothing to end turn):")
        if guess == "": return None
        word_i = dictionary.boardWordI(guess)
        if word_i is not None and board.canGuess(word_i):
            return board.findWord(word_i)
        else:                
            print ("Word cannot be guessed - it is not in the dictionary, not on the board, or is already revealed. Try again.")
            return self.guessWord(board, hint, remaining_guesses)

            
            
            
            
class Team:
    def playTurn(self, board : Board):
        pass
    
    def setTeam(self, team):
        self.team = team


class RealTeam(Team):
    captain : CaptainPlayer
    agent : AgentPlayer
    
    def __init__(self, captain, agent):
        self.captain = captain
        self.agent = agent
    
    def playTurn(self, board : Board):
        hint = self.captain.playTurn(board, self.team)
        self.agent.playTurn(board, hint, self.team)


class AutoTeam(Team):  
    def playTurn(self, board : Board):
        card = board.revealCardOfColor(self.team)
        print (f"Auto team plays, turning over {card.getStr(True)}. Current board:")
        ConsoleRenderer.render(board, False)
        press_enter_clear()
    
class Game:
    blue_team : Team
    red_team : Team
    
    def __init__(self, blue_team, red_team):
        blue_team.setTeam(BLUE)
        self.blue_team = blue_team
        red_team.setTeam(RED)
        self.red_team = red_team
        
    def playRound(self):
        blue_starts = random.random() < 0.5
        board = Board.randomBoard(blue_starts)
        blue_play = blue_starts
        while True:
            if blue_play:
                self.blue_team.playTurn(board)
            else:
                self.red_team.playTurn(board)
            if board.assassin_selected:
                print ("You selected the assassin!")
                
            if board.blue_won or not blue_play and board.assassin_selected:
                print (colored("Blue won the game", BLUE))
                break
            if board.red_won or blue_play and board.assassin_selected:
                print (colored("Red won the game", RED))
                break
            
            blue_play = not blue_play
                
        
        



if __name__ == "__main__":
    import main