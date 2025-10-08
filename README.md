# 🐍 Warwick AI Snake Competition 🏆

<div align="center">

<img width="452" height="449" alt="snakebr" src="https://github.com/user-attachments/assets/b60db513-3873-4d71-a567-10dcb9d06f86" />

### 🎮 **Welcome to the first ever WAI AI Programming Competition!** 🎮

[![Competition Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://warwick.ai)
[![Week](https://img.shields.io/badge/Deadline-Week%209%20Term%201-orange)](https://warwick.ai)
[![Prize](https://img.shields.io/badge/Prize-£50%20Tesco%20Voucher-gold)](https://warwick.ai)

</div>

---

Hello all and welcome to the first ever Warwick AI programming competition!

Don't worry if you're new to programming or AI, there's something here for everyone! For beginners, check out the WAI + Code Soc + UWCS Python course or ask us anything at our weekly code nights. See our [website](https://warwick.ai) for details.

### 🎯 Competition Highlights

- 🗺️ **Format:** Squad up in teams of any size!
- 🧠 **Duration:** Running officially till week 9 of term 1
- 💰 **Prize:** The winning team will receive a £50 Tesco Voucher + eternal WAI glory
- 📊 **Leaderboard:** Live updates on our website throughout the competition
- 🏆 **Final Testing:** We'll do thorough testing for final results

### 📝 Contributing

🤖 We want this repository to become place where future members can explore a variety of AI implementations and archetypes. 

❤️ Once the competition is over, we'd love to accept any and all creations as open source contributions! Your AI might even be used as a baseline for scoring future submissions!

✍️ Also, this is a also new project with room for improvement. If you have ideas or suggestions:
- ✉️ Message us directly
- 🚨 Send a pull request with your changes

Open source contributions are great practice and go an long way on a CV!

## 🛠️ Environment Setup

### Using the Template

First, login on our website https://warwick.ai with your GitHub account!  Don't worry if you forget, logging in later won't break anything :)

Next, use this template to create you own repository by pressing `Use this template`:      ⬇️

<img width="904" height="72" alt="template" src="https://github.com/user-attachments/assets/b05ccea8-bb53-4eed-ad5a-2de0b3a15b1d" />

Then, go to https://github.com/apps/warwickai and press install and authorise the app to view your repository.

<img width="452" height="170" alt="ghapp" src="https://github.com/user-attachments/assets/952fad17-b664-457f-982b-50cb5e42896a" />

With this done, submitting is as easy as pushing a commit to your repository!

If you don't have a development environment set up, an good alternative is making a github codespace:

<img width="452" height="431" alt="codespaces" src="https://github.com/user-attachments/assets/750288fb-c6ad-4602-9f36-08f53f8eaed2" />

### Installing Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

---

## 🎯 Running the Game

### Available Commands

#### 📋 List all difficulties
```bash
snake list
```

#### 👀 Watch your AI play
```bash
snake run easy
snake run hard
```

#### ⚡ Run headless tests
```bash
snake test 100 medium
snake test 50 all  # cycles through every difficulty
```

#### 🎲 Deterministic testing
```bash
snake run hard --seed 123
snake test 100 hard --seed 69
```

---

## 🧠 Writing Your AI

### The Basics
Your submission is the `myAI` function in `myAI.py`:

```python
def myAI(state: GameState) -> Turn:
    # Your brilliant strategy here!
    return Turn.LEFT  # or Turn.STRAIGHT or Turn.RIGHT
```

Your AI function should use the current state of the game `state` and ouput one of `Turn.LEFT`, `Turn.RIGHT` or `Turn.STRAIGHT`.

The turn you choose will make your snake turn left, right or stay straight before moving. 

### Some Inspiration

There's all sorts of ways to write an AI for this competition:
- Rules/heuristics
- Search algorithms
- Reinforcement learning
- and much more!

---

## 🏆 Submitting you AI

🐐 To submit your AI, simply push a commit to your repository. 

🧪 This will run some automated tests and your score will automatically appear on the website! <https://warwick.ai>

---

## 🚨 Important

Don't change anything in the snake folder as the submission tests use this code!

Other than this, have fun and see you at code nights! 

---

### Need Help?
- 📅 Weekly code nights
- 🌐 Visit [warwick.ai](https://warwick.ai)
- 💬 Message us with questions

---

<div align="center">

### 🏆 **Good luck and may the best snake win!** 🏆

</div>
