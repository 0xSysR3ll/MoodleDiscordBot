import yaml
import os
import sys



class Config:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

    def load(self):
        if not os.path.isfile(self.filename):
            sys.exit(f"{self.filename} not found! Please add it and try again.")
        else:
            with open(self.filename, 'r') as file:
                self.data = yaml.safe_load(file)

    def get_config(self, key, value):
        return self.data[key][value]