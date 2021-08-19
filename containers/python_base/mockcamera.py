class Color:
    def __init__(self, color):
        pass


class Preview:
    alpha = None

    def __init__(self):
        pass


class PiCamera:
    preview = Preview()

    def __init__(self):
        pass

    def start_recording(self, filename, sps_timing):
        pass

    def stop_recording(self):
        pass

    def close(self):
        pass

    def start_preview(self):
        pass

    def stop_preview(self):
        pass
