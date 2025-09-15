#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_yaml(yaml_path: Path) -> dict:
    with yaml_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(instance: dict, schema: dict) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        lines = [
            "Input YAML failed schema validation:",
        ]
        for err in errors:
            location = "/".join([str(p) for p in err.path]) or "<root>"
            lines.append(f"- {location}: {err.message}")
        raise SystemExit("\n".join(lines))


def render_html(data: dict, template_dir: Path, template_name: str) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate AI System Card HTML from YAML + JSON Schema")
    parser.add_argument("yaml", type=Path, help="Path to system card YAML data")
    parser.add_argument("schema", type=Path, help="Path to JSON schema file")
    parser.add_argument("--template", type=Path, default=Path("templates/system_card.html.j2"), help="Path to Jinja2 template")
    parser.add_argument("--output", type=Path, default=Path("build/system_card.html"), help="Output HTML path")

    args = parser.parse_args(argv)

    data = load_yaml(args.yaml)
    schema = load_json(args.schema)

    validate_schema(data, schema)

    template_dir = args.template.parent
    template_name = args.template.name
    html = render_html(data, template_dir, template_name)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


