from app.application import App
import traceback


def main():
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()