from app.application import App

OPEN_GUI = True

if __name__ == "__main__":
    if OPEN_GUI:
        app = App()
        app.mainloop()
