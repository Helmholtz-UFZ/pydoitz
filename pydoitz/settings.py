import pydoitz
from pydoitz import utils


class LoginEntry:

    def __init__(self, host, user, password, is_default, key):
        self.host = host
        self.user = user
        self.password = password
        self.is_default = is_default
        self.key = key

    def get_credential(self, attr):
        if attr.startswith("KEYRING@"):
            import keyring
            service = attr.split("@")[1]
            return keyring.get_password(service, self.user)

        return attr


class LoginFile:

    def __init__(self, path=None):
        self.entries = []
        self.path = utils.get_config_file(path, "login")
        self._parse_file()

    @property
    def default_entry(self):
        for entry in self.entries:
            if entry.is_default:
                return entry

    def find_entries(self, host, user):
        matching_entries = []
        if not host and not user:
            return [self.default_entry]

        for entry in self.entries:
            if (host and entry.host == host
                    or user and entry.user == user and entry.host == host):
                matching_entries.append(entry)

        return matching_entries

    def _parse_file(self):
        if not self.path or not self.path.exists():
            return None

        parser = utils.CONFIG_FORMATS[self.path.suffix[1:]]["parser"]

        with self.path.open() as f:
            data = parser.safe_load(f)
            default_found = False

            for item in data:
                entry = LoginEntry(
                    host=item.get("host"),
                    user=item.get("user"),
                    password=item.get("password"),
                    is_default=item.get("default"),
                    key=item.get("key")
                )
                if entry.is_default:
                    if default_found:
                        raise ValueError("There can only be one default entry.")
                    default_found = True

                self.entries.append(entry)


class CategoryConfigEntry:

    def __init__(self, name, cli_name, fields):
        self.name = name
        self.cli_name = cli_name
        self.fields = fields

    def merge(self, user_entry):
        if user_entry.cli_name:
            self.cli_name = user_entry.cli_name

        for param in list(self.fields.keys()):
            user_data = user_entry.fields.get(param, {})
            cache_data = self.fields.get(param, {})
            self.fields[param] = {**cache_data, **user_data}


class CategoryConfig:

    def __init__(self, path=None, host=None):
        self.user_conf = utils.get_config_file(path, "categories")
        self.user_conf_exists = self.user_conf.exists()
        if host:
            self.cache_conf = utils.get_cache(host) / "categories.json"
        else:
            self.cache_conf = None

        self.entries = self._parse(self.cache_conf)
        user_entries = self._parse(self.user_conf)
        for entry_name, entry in user_entries.items():
            if entry_name in self.entries:
                self.entries[entry_name].merge(entry)
            self.entries[entry_name] = entry

    def __contains__(self, entry):
        return True if entry.name in self.entries else False

    def get(self, name):
        return self.entries.get(name)

    def get_by_cli(self, name):
        for item in self.entries.values():
            if item.cli_name == name:
                return item
        return None

    def _parse(self, path):
        if not path or not path.exists():
            return {}

        parser = utils.CONFIG_FORMATS[path.suffix[1:]]["parser"]

        entries = {}
        with path.open() as f:
            data = parser.load(f)
            added = []

            for item in data:
                entry = CategoryConfigEntry(
                    name=item.get("name"),
                    cli_name=item.get("cli_name"),
                    fields=item.get("params")
                )
                if entry.name not in entries:
                    entries[entry.name] = entry
        return entries

    def remap_keys(self, name, fields):
        if not self.user_conf_exists:
            return fields

        entry = self.get(name)
        out = {}
        for cli_arg, cli_val  in fields.items():
            for api_arg, data in entry.fields.items():
                if cli_arg == data.get("param") and cli_val:
                    out[api_arg] = cli_val
        return out
