from framework.components.profile import Profile
from framework.components.test_case import TestCase


class CLC_Profile(Profile):
    mongo_client_name = "mongodb://QA-TestMongo:27017"
    mongo_database_name = "TestMFG"
    mongo_collection_name = "TestRecords3"
    Description = "CLC Profile"

    def __init__(self, dut, jig, prompt_function=None):
        super(CLC_Profile, self).__init__(dut)