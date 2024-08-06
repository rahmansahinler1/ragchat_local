from pathlib import Path

from prefect.deployments import Deployment
from prefect import flow

from tasks.file_detection_task import FileDetectionTask


class DBFileDetectionFlow:
    """
    A class to manage file detection flows using Prefect.

    This class handles the configuration and execution of file detection tasks,
    as well as the creation of Prefect deployments.

    Attributes:
        main_folder (Path): The root folder of the project.
        db_folder (Path): The folder to be monitored for changes.
        deployment_name (str): The name of the Prefect deployment.
        interval (int): The interval between flow runs in seconds.
        duration (int): The duration of each file detection task in seconds.
        file_detection_task (FileDetectionTask): The task responsible for detecting file changes.
    """

    def __init__(
            self,
            interval = 90,
            duration = 60,
        ):
        """
        Initialize the DBFileDetectionFlow.

        Args:
            interval (int): The interval between flow runs in seconds. Default is 600 (10 minutes).
            duration (int): The duration of each file detection task in seconds. Default is 300 (5 minutes).
        """
        self.main_folder = Path(__file__).resolve().parent.parent
        self.db_folder = self.main_folder / "db" / "domains"
        self.deployment_name = "DB File Detection"
        self.interval = interval
        self.duration = duration
        self.file_detection_task = FileDetectionTask(database_folder_path=self.db_folder)
    
    def run_detection(self):
        """
        Execute the file detection task and print the detected changes.

        Returns:
            list: A list of detected file changes.
        """
        changes = self.file_detection_task.get_changes()
        for change in changes:
            print(change)
        return changes

    def create_deployment(self):
        """
        Create and apply a Prefect deployment for the file detection flow.

        This method builds a deployment using the standalone db_file_detection_flow function
        and applies it to the Prefect server.
        """
        deployment = Deployment.build_from_flow(
            flow=db_file_detection_flow,
            name="DB File Detection",
            schedule={"interval": self.interval},
            work_queue_name="db_file_detection"
        )
        deployment.apply()

@flow
def db_file_detection_flow():
    """
    Prefect flow that runs the file detection task.
    This standalone function serves as the entry point for Prefect to execute the flow.

    Returns:
        list: A list of detected file changes.
    """
    detector = DBFileDetectionFlow()
    return detector.run_detection()
