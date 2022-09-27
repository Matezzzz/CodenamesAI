from players import Game
from datasets import CombinedInitializer


#let user define both teams
game = Game.createGameInput(CombinedInitializer.DefaultInitializer())

#create a game with given teams
#game = Game.createGame(Game.TEAM_AI_H, Game.TEAM_AUTO, CombinedInitializer.DefaultInitializer())

#play 1 game
game.playRound()

