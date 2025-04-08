from openproductapiclient.models import Configuration


def get_open_product_client():
    return Configuration.get_solo().client
