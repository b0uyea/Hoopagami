player = input("Player name: ")

points = input("Points: ")
rebounds = input("Rebounds: ")
assists = input("Assists: ")
steals = input("Steals: ")
blocks = input("Blocks: ")

statline = f"{points}-{rebounds}-{assists}-{steals}-{blocks}"

with open("statlines.txt", "a") as file:
    file.write(player + " | " + statline + "\n")

with open("statlines.txt", "r") as file:
    lines = file.read().splitlines()

count = 0

for line in lines:
    if line.endswith(statline):
        count += 1

print("")
print("Player:", player)
print("Statline:", statline)
print("This statline has occurred", count, "time(s).")
