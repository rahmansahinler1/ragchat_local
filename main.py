from app.application import App
from flows.detection_flow import DBFileDetectionFlow

CREATE_DEPLOYMENT = True
OPEN_GUI = False

if __name__ == "__main__":
    if OPEN_GUI:
        app = App()
        app.mainloop()

    if CREATE_DEPLOYMENT:
        deployment = DBFileDetectionFlow()
        deployment.create_deployment()

# TODO: Test it with larger pdf
# TODO: Indexing with more than one pdf
# TODO: Search with more than one pdf
# TODO: Add index metadata
