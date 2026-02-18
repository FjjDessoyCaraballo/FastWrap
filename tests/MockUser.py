import random
import string

class MockUser():
    def __init__(self):
        self.id: str = ''
        self.email: str = self.generate_random_email()
        self.password: str = self.generate_random_password()
        self.api_key: str = ''
        self.character: str = 'You are a botanist who sells flowers.'
        self.character_id: str = ''

    def generate_random_email(self) -> str:
        random_string: str = ''.join(random.choices(string.ascii_letters, k=10))
        random_email: str = random_string + "@example.com"
        return random_email

    def generate_random_password(self) -> str:
        random_lower_string: str = ''.join(random.choices(string.ascii_lowercase, k=3))
        random_upper_string: str = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_number: str = ''.join(random.choices(string.digits, k=4))
        special_case: str = "!"

        random_password: str = random_lower_string + random_upper_string + random_number + special_case

        return random_password

