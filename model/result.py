class Result:
    def __init__(self, success: bool, result):
        self.success = success
        self.result = result

    @staticmethod
    def get_positive(result=None):
        return Result(True, result)

    @staticmethod
    def get_negative(result=None):
        return Result(False, result)
