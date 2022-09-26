from players import AIAgentPlayer, AICaptainPlayer, CaptainPlayer, Game, AutoTeam, RealTeam, HumanAgentPlayer, HumanCaptainPlayer
from datasets import WordCollocationsInitializer, SentenceCollocationsInitializer, FastTextInitializer, WordAssociationInitializer, CombinedInitializer, DoubleLinkInitializer
from model import AgentModel, CaptainModel


BEST_FASTTEXT_THRESHOLD = 0.685

#create a combined initializer from all basic datasets
basic = CombinedInitializer([WordCollocationsInitializer(), SentenceCollocationsInitializer(), FastTextInitializer(BEST_FASTTEXT_THRESHOLD), WordAssociationInitializer()], [1, 0.5, 0.75, 1])

#create a combined dataset of the basic dataset and the double link initializer of the basic dataset
combined = CombinedInitializer([basic, DoubleLinkInitializer(basic)], [1.0, 1.0])

#create a game with given teams
game = Game.createGameInput(combined)
#game = Game.createGame(Game.TEAM_AI_H, Game.TEAM_AUTO, combined)
#play 1 game
game.playRound()

