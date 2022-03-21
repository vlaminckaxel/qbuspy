class QBusResponseException(Exception):
    def __init__(self, error_code: int):
        self.error_code = error_code
        if error_code == 1:
            msg = "The controller is busy, please try again later"
        elif error_code == 2:
            msg = "Your session timed out. Please login again"
        elif error_code == 3:
            msg = "Too much devices are connected to the controller."
        elif error_code == 4:
            msg = "The controller was unable to execute your command."
        elif error_code == 5:
            msg = "Your session could not be started"
        elif error_code == 6:
            msg = "The command is unknown"
        elif error_code == 7:
            msg = "No EQOweb configuration found, please run System manager to upload and configure EQOweb."
        elif error_code == 8:
            msg = "System manager is still connected. Please close System manager to continue"
        else:
            msg = "Undefined error in the controller. Please try again later"
        super().__init__(msg)


class QbusCredentialException(Exception):
    pass
