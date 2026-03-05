import json
from typing import Dict
from pydantic import BaseModel, Field
from cat import plugin, log
from cat.db.cruds import plugins as crud_plugins
from cat.services.string_crypto import StringCrypto


crypto = StringCrypto()


class CatWithGoogleDriveSettings(BaseModel):
    """Settings for the Cat with Google Drive plugin."""
    service_account_json: str = Field(
        title="Google Service Account JSON",
        description="Content of the JSON file of the Service Account from Google Cloud",
        default=""
    )


@plugin
def settings_schema():
    return CatWithGoogleDriveSettings.model_json_schema()


@plugin
def load_settings(plugin_id: str, agent_id: str) -> Dict:
    global crypto

    settings = crud_plugins.get_setting(agent_id, plugin_id)
    if not settings:
        return {"service_account_json": {}}

    try:
        service_account_json_value = crypto.decrypt(settings.get("service_account_json", ""))
        service_account_json_value = json.loads(service_account_json_value)
    except json.JSONDecodeError:
        service_account_json_value = {}

    return {"service_account_json": service_account_json_value}


@plugin
def save_settings(plugin_id: str, settings: Dict, agent_id: str) -> Dict:
    global crypto

    service_account_json = settings.get("service_account_json")
    if not service_account_json:
        raise ValueError("Service Account JSON is required")

    try:
        service_account_json_value = json.dumps(service_account_json)

        service_account_json = {
            "service_account_json": crypto.encrypt(service_account_json_value)
        }
        crud_plugins.set_setting(agent_id, plugin_id, service_account_json)
        return service_account_json
    except Exception as e:
        log.error(f"Error serializing Service Account JSON: {e}")
        raise ValueError(f"Failed to save settings: {e}") from e
