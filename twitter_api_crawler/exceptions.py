class TwitterNoAvailableAPIs(Exception):
    pass

class Twitter429Exception(Exception):
    pass


class Twitter404Exception(Exception):
    pass


class Twitter503Exception(Exception):
    pass


class TwitterAPIClientException(Exception):
    pass
