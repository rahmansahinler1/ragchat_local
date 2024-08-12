from app.application import App
from pipeline_setup.data_pipeline import FileDetectionFlow


CREATE_DEPLOYMENT = False
OPEN_GUI = False

if __name__ == "__main__":
    if OPEN_GUI:
        app = App()
        app.mainloop()

    if CREATE_DEPLOYMENT:
        detection_flow = FileDetectionFlow(interval=600)
        detection_flow.create_deployment()
