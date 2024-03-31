from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import SubscriptionClient
import requests
import json

CONFIG_DICT = {}

# Authenticate and create a management client
credential = DefaultAzureCredential()
subscription_client = SubscriptionClient(credential)

for subscription in subscription_client.subscriptions.list():

# Create a WebSiteManagementClient instance
    website_client = WebSiteManagementClient(credential, subscription.subscription_id)

    # List all App Services in the subscription
    app_services = website_client.web_apps.list()

    # Iterate over the App Services and print their application settings
    for app_service in app_services:
        print(f"App Service Name: {app_service.name}")
        # print(f"Resource Group: {app_service.resource_group}")

        # Get the application settings for the App Service
        app_settings = website_client.web_apps.list_application_settings(
            resource_group_name=app_service.resource_group,
            name=app_service.name
        )

        # print("Application Settings:")
        for setting, value in app_settings.properties.items():
            if setting == "CONFIG_URL":
                print(f"Config URL: {value}")
                config_file = requests.get(value)
                config_dict = json.loads(config_file.text)
                print("-----------------")
                print("Mixpanel Key")
                print(config_dict['tracker']['token'])
                print("-----------------")
                
