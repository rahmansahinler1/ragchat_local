from dotenv import load_dotenv

from app.application import App

import os

if __name__ == "__main__":
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    app = App()
    app.mainloop()
