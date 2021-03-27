class Address:
    def __init__(self, value, mapping=None):
        self.address = value
        self.mapping = mapping

    def set_mapping(self, mapping):
        self.mapping = mapping

    def __getattr__(self, item):
        if item in self.mapping:
            return self.address & self.mapping[item]
