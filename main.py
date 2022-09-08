from players import AIAgentPlayer, AICaptainPlayer, CaptainPlayer, Game, AutoTeam, RealTeam, HumanAgentPlayer, HumanCaptainPlayer
from datasets import WordCollocationsInitializer, SentenceCollocationsInitializer, FastTextInitializer, WordAssociationInitializer, CombinedInitializer
from model import AgentModel, CaptainModel

#best fasttext = 0.685
combined = CombinedInitializer([WordCollocationsInitializer(), SentenceCollocationsInitializer(), FastTextInitializer(0.685), WordAssociationInitializer()], [1, 0.5, 0.75, 1])

blue_team = RealTeam(AICaptainPlayer(CaptainModel(combined, reveal_hinted=False)), HumanAgentPlayer())
#blue_team = RealTeam(HumanCaptainPlayer(), AIAgentPlayer(AgentModel(FastTextInitializer())))
#blue_team = RealTeam(AICaptainPlayer(CaptainModel(FastTextInitializer())), AIAgentPlayer(AgentModel(FastTextInitializer())))


red_team = AutoTeam()
game = Game(blue_team, red_team)
game.playRound()

#! GPT-2 + prompts
#! use pointwise mutual information for word/sentence collocs
#! filter
#! END WHEN ASSASSIN IS SELECTED