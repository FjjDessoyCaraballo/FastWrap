import questionary

answer: str = questionary.text("Do you want to run the wizard?").ask()



print(answer.lower().strip(' '))