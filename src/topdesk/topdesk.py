import json
import requests
from requests.auth import HTTPBasicAuth
import logging

"""
Configure Logging
"""
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class topdesk():
    def __init__(self, config):
        """
        :param config: Config File with username, password and Base URL
        {
        "username":"admin",
        "password":"1234",
        "base_url":"topdesk.host"
        }
        """
        self.username = config["username"]
        self.password = config["password"]
        self.base_url = "https://" + config["base_url"] + "/tas/api/"

    def td_get(self, path, td_filter="", fields=None, archived=None):
        """
        :param archived: If True only Archived records will be returned, on false only not archived records will be returned. None for all records
        :param fields: Comma seperated list of fields that you want to get from API
        :param path: API Path to get
        :param td_filter: Filter for API Path
        :param output: Output Array
        :return: Returns array of Data
        """
        default_fields = "type,@status,archived,name,host-name,@assignments,mac-address,ip-address,host-group,technical-owner,discovery-host-name,mem-device-name"
        if not fields:
            fields = default_fields
        params = {
            "fields": fields,
            "$orderby": "name asc",
            "archived": archived,
            "pageSize": 1000,
            "pageStart": 0
        }
        if td_filter:
            params["$filter"] = td_filter
        url = self.base_url + path
        output = []
        while True:
            response = requests.get(url, auth=HTTPBasicAuth(self.username, self.password), params=params)
            if response.status_code == 206:
                output = output + response.json()["dataSet"]
                params["pageStart"] += params["pageSize"]
            if response.status_code == 200:
                dataset = response.json()["dataSet"]
                if len(dataset) > 0:
                    output = output + dataset
                break
        return output

    def get_assets(self, fields=None, archived=False, td_filter=None):
        """
        :return: Returns all assets found
        """
        return self.td_get("assetmgmt/assets", fields=fields, archived=archived, td_filter=td_filter)

    def update_asset(self, asset_id, payload, asset_name="N/A"):
        url = self.base_url + "assetmgmt/assets/" + asset_id
        logger.debug(url)
        params = {"excludeActions": "false"}
        response = requests.request("POST",
                                    url,
                                    json=payload,
                                    auth=HTTPBasicAuth(self.username, self.password),
                                    params=params)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 202:
            logger.warning(f"Asset {asset_name} cannot be update with these values because fields don't exist")
            return response.json()
        else:
            try:
                response = response.json()
            except Exception as e:
                logger.error("Failed to json decode response from Topdesk")
                logger.debug(e)
                logger.debug(response.text)
                logger.error(response.url)
                logger.error(response.status_code)
                return False
            if response["pageError"] == "Diese Karte ist zwischenzeitlich geändert worden.":
                logger.debug(f"Unable to update asset {asset_name} because it is disabled")
            else:
                logger.error(f"Failed to update asset {asset_name}")
                logger.error(response)
            return False
