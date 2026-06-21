import json

class FeatureToggle:
    features = {}

    @classmethod
    def loadFromFile(cls, config_path):
        with open(config_path, 'r') as f:
            cls.features.update(json.load(f))

    @classmethod
    def isEnabled(cls, feature_name):
        return cls.features.get(feature_name, True)

    @classmethod
    def isDisabled(cls, feature_name):
        return not cls.isEnabled(feature_name)
    
    @classmethod
    def getFeatureValue(cls, feature_name):
        return cls.features.get(feature_name, 0)