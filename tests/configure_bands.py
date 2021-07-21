class SampleBands:
    @staticmethod
    def basic_config():
        return {
            "buyBands": [
                {
                    "minMargin": 0.005,
                    "avgMargin": 0.01,
                    "maxMargin": 0.02,
                    "minAmount": 20.0,
                    "avgAmount": 30.0,
                    "maxAmount": 40.0,
                },
            ],
            "sellBands": [
                {
                    "minMargin": 0.005,
                    "avgMargin": 0.01,
                    "maxMargin": 0.02,
                    "minAmount": 20.0,
                    "avgAmount": 30.0,
                    "maxAmount": 40.0,
                },
            ],
        }