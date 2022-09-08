# Codenames AI

## Running

In addition to the source code available here, you need to download the required datasets. These can be downloaded here : [mega.nz](https://mega.nz/file/9kFWwRiL#0Rmn0a6Qo1UM-lqRW47qIK1oQRLYU6h6j43tBel_rHc). They should be unzipped, and pasted into the project directory. (if */project/main.py* is the path to the main file, */project/data/* directory should exist too, and contain *word_associations.npy*, *board_words_en.txt* and other files)

After that, run the *main.py* python file in the project directory to run the app.


## Required libraries

I use the following packages:
* numpy
* scipy
* Levenshtein (for the levenshtein metric. [Link](https://pypi.org/project/Levenshtein/))
* colorama (for printing colored text. [Link](https://pypi.org/project/colorama/))
