# Discord Bot Word Game - English

## Table of Contents
- [Discord Bot Word Game - English](#discord-bot-word-game---english)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Rules for Turkish Words](#rules-for-turkish-words)
  - [Development Status](#development-status)
  - [How to Use](#how-to-use)
  - [Contributing](#contributing)
  - [Word List](#word-list)
  - [Note](#note)

## Introduction
This Discord bot allows you to play a word game based on Turkish words. In the game, a user writes a word, and the next user must write a new word that starts with the last letter of the previous word. However, only Turkish words are accepted, and they must follow specific Turkish language rules.

## Rules for Turkish Words
For a word to be valid in the game, it must meet the following rules:

1. **Word List**: The word must be in the `word.txt` file. This file contains a list of Turkish words.
2. **Syllable Rule**: The word should not have 'o' or 'ö' in any syllable except the first one. This rule is used to ensure that the word is originally Turkish.
3. **Long Vowels**: The word should not contain long vowels like 'â', 'î', 'û'. These vowels are typically found in loanwords from Arabic or Persian.
4. **Case Insensitivity**: Words are checked without regard to case, i.e., all words are converted to lowercase.

## Development Status
This bot is still under development and may contain errors. Particularly, the syllable splitting algorithm is simple and may not always be accurate. Additionally, the word list is not comprehensive and more words can be added.

## How to Use
- To add the bot to your server, create a bot on the Discord Developer Portal and get its token.
- Replace `YOUR_BOT_TOKEN` in the `main.py` file with your bot token.
- Run the bot using the command `python main.py`.
- Start the game with the command `/kelimeoyunu`.
- End the game with the command `/bitir`.
- During the game, you can play by writing valid Turkish words.

## Contributing
This project is open source, and we welcome your contributions. If you find any bugs or want to add new features, please send a pull request on GitHub.

## Word List
- The `word.txt` file contains the valid words for the game.
- You can add new words to this file, but make sure they are Turkish words.

## Note
This bot is still being developed by the developer and may contain errors. If you encounter any issues, please report them to the developer or contribute by fixing them.