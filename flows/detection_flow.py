from pathlib import Path

from prefect.deployments import Deployment
from prefect import flow

from tasks.file_detection_task import FileDetectionTask


class DBFileDetectionFlow:
    def __init__(
            self,
            interval = 600,
            duration = 300,
        ):
        self.main_folder = Path(__file__).resolve().parent
        self.db_folder = self.main_folder / "db"
        self.deployment_name = "DB File Detection"
        self.interval = interval
        self.duration = duration
        self.file_detection_task = FileDetectionTask(database_folder_path=self.db_folder)

    @flow
    def db_file_detection_flow(self):
        """
        Prefect flow that runs the detect_changes task.
        """
        changes = self.file_detection_task.get_changes()
        for change in changes:
            print(change)
        return changes

    def create_deployment(self):
        deployment = Deployment.build_from_flow(
            flow=self.db_file_detection_flow,
            name="DB File Detection",
            parameters={"db_path": self.db_folder},
            schedule={"interval": self.interval},
            work_queue_name="db_file_detection"
        )

        deployment.apply()
