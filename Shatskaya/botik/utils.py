import random

def generate_code():
    return str(random.randint(10000, 99999))

def shuffle_participants(participants):
    shuffled = participants.copy()   
    while True:
        random.shuffle(shuffled)
        if all(shuffled[i] != participants[i] for i in range(len(participants))):
            break
            
    return shuffled
