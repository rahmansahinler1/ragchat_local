import tkinter as tk
from tkinter import *

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hello, World!")
        self.geometry("400x200")
        self.label = tk.Label(self, text="Hello, World!")
        self.label.pack(pady=20)

        self.button = tk.Button(self, text="Click Me!", command=self.say_hello)
        self.button.pack(pady=20)

    def say_hello(self):
        self.label.config(text="Hello, World! from the button")