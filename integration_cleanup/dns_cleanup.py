from instance.gandi import api


class GandhiCleanup:
    """
    Handles the cleanup of dangling DNS entries
    """
    def __init__(self, api_key, dry_run=False):
        """
        Dummy method for now
        """
        self.dry_run = dry_run

    def run_cleanup(self):
        """
        Runs the actual cleanup
        """
        pass
