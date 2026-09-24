"""Safe YAML loading with duplicate-key rejection."""

import yaml


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in result:
                    raise ValueError(f"duplicate YAML key: {key}")
                result[key] = self.construct_object(value_node, deep=deep)
            except TypeError as exc:
                raise ValueError("YAML keys must be scalar values") from exc
        return result


def load_yaml(text: str):
    return yaml.load(text, Loader=UniqueLoader)
