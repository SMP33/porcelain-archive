"""Перегенерирует config.py (объявления атрибутов) на основе структуры config.ini."""
import configparser
import os
import sys

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")


def _is_numeric_field(key: str) -> bool:
    # Тип определяется по имени ключа, а не по значению - иначе секрет,
    # случайно состоящий из цифр (например, пароль "123"), станет числом.
    key = key.lower()
    return key == "port" or key.endswith("_port")


def generate(ini_path: str) -> str:
    parser = configparser.ConfigParser()
    if not ini_path or not parser.read(ini_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {ini_path}")

    lines = ["import configparser", "import os", "", ""]
    sections = []
    for section_name in parser.sections():
        class_name = f"{section_name.capitalize()}Config"
        sections.append((section_name, class_name))

        lines.append(f"class {class_name}:")
        for key in parser.options(section_name):
            value_type = "int" if _is_numeric_field(key) else "str"
            lines.append(f"    {key}: {value_type}")
        lines.append("")
        lines.append("")

    lines.append("class Config:")
    for section_name, class_name in sections:
        lines.append(f"    {section_name.lower()}: {class_name}")
    lines.append("")
    lines.append("    def __init__(self, path: str):")
    lines.append("        parser = configparser.ConfigParser()")
    lines.append("        if not path or not parser.read(path):")
    lines.append('            raise FileNotFoundError(f"Файл конфигурации не найден: {path}")')
    lines.append("")
    for section_name, class_name in sections:
        attr = section_name.lower()
        lines.append(f"        self.{attr} = {class_name}()")
        for key in parser.options(section_name):
            getter = "getint" if _is_numeric_field(key) else "get"
            lines.append(f"        self.{attr}.{key} = parser.{getter}({section_name!r}, {key!r})")
        lines.append("")
    lines.append("")
    lines.append("config = Config(os.environ.get('ARCHIVE_CONFIG_INI_PATH'))")
    lines.append("")

    return "\n".join(lines)


def regenerate(ini_path: str = None) -> str:
    """Перегенерирует config.py по ini_path (или ARCHIVE_CONFIG_INI_PATH, или .secret/config.ini)."""
    if not ini_path:
        ini_path = os.environ.get("ARCHIVE_CONFIG_INI_PATH") or "./.secret/config.ini"

    content = generate(ini_path)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return ini_path


if __name__ == "__main__":
    ini_path = regenerate()
    print(f"config.py обновлён по {ini_path}")
