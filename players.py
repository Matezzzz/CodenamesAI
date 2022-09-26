from telnetlib import GA
from common import *

from board import Board
from model import AgentModel, CaptainModel, Hint
from renderer import ConsoleRenderer, colored, clear


class CaptainPlayer:
    team : int = UNKNOWN
    
    #play turn = give one hint
    def playTurn(self, board : Board, team : int):
        print (f"Current turn: {colored('Captain', team)}")
        #give hint will be overriden for all types of players (AI or human)
        hint = self.giveHint(board, team)
        #disable given hint - it cannot be said again
        board.disableHint(hint.word_i)
        print (f"Given hint: {hint.colored(team)}")
        #when user presses enter, clear the screen. Agent will play next
        press_enter_clear()
        return hint
    
    #will be overriden by all child classes
    def giveHint(self, board : Board, team : int):
        return Hint.Invalid()
    

class AICaptainPlayer(CaptainPlayer):
    model : CaptainModel
    
    def __init__(self, model):
        self.model = model
    
    #give hint = use my model to generate a hint
    def giveHint(self, board : Board, team : int) -> Hint:
        return self.model.giveHint(team, board)
    

class HumanCaptainPlayer(CaptainPlayer):
    def giveHint(self, board : Board, team : int) -> Hint:
        #if playing human + human, print a warning, so the agent doesn't see the board by mistake
        input("Press ENTER to show the board, with colored roles")
        #print current board
        print (f"Current board:")
        ConsoleRenderer.render(board, True)
        #human will try giving a hint. If it is not present in the dictionary, he will try again
        while True:
            hint = input ("The hint to give: ")
            hint_i = dictionary.hintWordI(hint)
            if hint_i != -1:
                break
            else:
                print ("This word isn't in the dictionary - AI models cannot guess based on it, try another one. Sorry :(")
        #human will try entering a number of words associated with this hint. If invalid, he will try again
        while True:
            try:
                count = int(input ("How many words are related to this hint: "))
                break
            except ValueError:
                print ("Given value must be an integer. Try again.")
        #return the given hint
        return Hint(hint_i, count)




class AgentPlayer:
    #play turn -  guess words associated with the given hint
    def playTurn(self, board : Board, hint : Hint, team : int):
        print (f"Current turn: {colored('Agent', team)}")
        #make all the guesses
        self.guess(board, hint, team)
        #print the board after turn
        print ("Board after turn:")
        ConsoleRenderer.render(board, False)
        press_enter_clear()
    
    def guess(self, board : Board, hint : Hint, team : int):
        #cycle over remaining hints count
        for rem_hints in range(hint.count + 1, 0, -1):
            #print given hint
            print (f"Given hint: {hint.colored(team)}, Remaining guesses: {rem_hints - 1} + {1}")
            #guess one word (will be overriden by child classes)
            card_i = self.guessWord(board, hint, rem_hints)
            #if no card was guessed, stop guessing
            if card_i == None: break
            #else, reveal the given card
            role = board.reveal(card_i)
            word = role.getStr(True)
            #print a message based on whether my guess was correct or not
            if role.role != team:
                print (f"Guessed a wrong word ({word}). Your turn ends.")
                break
            else:
                print (f"Guessed correctly ({word})")
            if board.game_ended: break
    
    #will be overriden by child classes
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        return None
        
    
    
class AIAgentPlayer(AgentPlayer):
    model : AgentModel
    
    def __init__(self, model):
        self.model = model
    
    #use the agent model to guess a word
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        return self.model.guess(board, hint)
    


class HumanAgentPlayer(AgentPlayer):
    def guessWord(self, board : Board, hint : Hint, remaining_guesses : int):
        #print current board
        print("Current board:")
        ConsoleRenderer.render(board, False)
        #let the player guess
        guess = input("Guess(Nothing to end turn):")
        #if nothing was given, end turn
        if guess == "": return None
        #else, check whether the guess is valid (it must be on the board and in the dictionary). If yes, return it, if not, run this method again
        word_i = dictionary.boardWordI(guess)
        if word_i is not None and board.canGuess(word_i):
            return board.findWord(word_i)
        else:
            print ("Word cannot be guessed - it is not in the dictionary, not on the board, or is already revealed. Try again.")
            return self.guessWord(board, hint, remaining_guesses)


class Team:
    #play 1 turn - captain gives a hint and an agent guesses words based on it    
    def playTurn(self, board : Board):
        pass
    
    #set team color
    def setTeam(self, team):
        self.team = team

#real team - consists of a captain and an agent
class RealTeam(Team):
    captain : CaptainPlayer
    agent : AgentPlayer
    
    def __init__(self, captain, agent):
        self.captain = captain
        self.agent = agent
    
    def playTurn(self, board : Board):
        #captain gives a hint
        hint = self.captain.playTurn(board, self.team)
        #and agent guesses based on it
        self.agent.playTurn(board, hint, self.team)

#auto team - turn over one friendly card every turn
class AutoTeam(Team):  
    def playTurn(self, board : Board):
        #reveal a card
        card = board.revealCardOfColor(self.team)
        #print the board to tell others what was revealed
        print (f"Auto team plays, turning over {card.getStr(True)}. Current board:")
        ConsoleRenderer.render(board, False)
        press_enter_clear()


#holds two teams, can play a game with both of them
class Game:
    blue_team : Team
    red_team : Team
    
    #save given teams and assign their colors
    def __init__(self, blue_team, red_team):
        blue_team.setTeam(BLUE)
        self.blue_team = blue_team
        red_team.setTeam(RED)
        self.red_team = red_team
        
    
    def playRound(self):
        #select a starting team, create the initial board accordingly
        blue_starts = random.random() < 0.5
        board = Board.randomBoard(blue_starts)
        blue_play = blue_starts
        while True:
            #if blue should play, let blue play a turn. Else let red
            if blue_play:
                self.blue_team.playTurn(board)
            else:
                self.red_team.playTurn(board)
                
            #print a message if assassin was selected
            if board.assassin_selected: print ("You selected the assassin!")
            
            #if either team won (they have no cards hidden, or the opposing team selected the assassin), print a message and end the game
            if board.blue_won or not blue_play and board.assassin_selected:
                print (colored("Blue won the game", BLUE))
                break
            if board.red_won or blue_play and board.assassin_selected:
                print (colored("Red won the game", RED))
                break
            #let the other team play
            blue_play = not blue_play
    
    #constants for creating a team automatically
    TEAM_AUTO = 0
    TEAM_AI_H = 1
    TEAM_H_AI = 2
    TEAM_H_H = 3
    @staticmethod
    def createTeam(team_type, ai_initializer):
        #create a team based on the integers above
        if team_type == Game.TEAM_AUTO: return AutoTeam()
        return RealTeam(
            AICaptainPlayer(CaptainModel(ai_initializer)) if team_type == Game.TEAM_AI_H else HumanCaptainPlayer(),
            AIAgentPlayer(AgentModel(ai_initializer)) if team_type == Game.TEAM_H_AI else HumanAgentPlayer()
        )

    #let user input values into the console to create a team as they wish
    @staticmethod
    def createTeamInput(team_name, ai_initializer):
        print (f"Create {team_name} team:")
        #let user enter a team type
        team_type = int(input(f"Define team type:\n * {Game.TEAM_AUTO} for AutoTeam\n * {Game.TEAM_AI_H} for AI+human\n * {Game.TEAM_H_AI} for human+AI\n * {Game.TEAM_H_H} for human+human\nTeam type:"))
        #return the created team
        return Game.createTeam(int(team_type), ai_initializer)
    
    #create a game with given team types and ai initializer
    @staticmethod
    def createGame(team1, team2, ai_initializer):
        return Game(Game.createTeam(team1, ai_initializer), Game.createTeam(team2, ai_initializer))
    
    #create a game with both teams specified via console
    @staticmethod
    def createGameInput(ai_initializer):
        return Game(Game.createTeamInput("blue", ai_initializer), Game.createTeamInput("red", ai_initializer))

    


if __name__ == "__main__":
    import main