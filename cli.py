import json
import os
import click
from pathlib import Path

DATA_DIR = Path(os.getenv("STUDYMAP_DATA_DIR", "./data"))


def _course_path(course: str) -> Path:
    return DATA_DIR / course.replace(" ", "_")


def _load_nodes(course: str):
    from store.schema import KnowledgeNode
    p = _course_path(course) / "framework.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [KnowledgeNode(**n) for n in data]


def _save_nodes(course: str, nodes):
    from dataclasses import asdict
    p = _course_path(course)
    p.mkdir(parents=True, exist_ok=True)
    (p / "framework.json").write_text(
        json.dumps([asdict(n) for n in nodes], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _load_rhetoric(course: str):
    from store.schema import RhetoricEntry
    p = _course_path(course) / "rhetoric.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [RhetoricEntry(**r) for r in data]


@click.group()
def cli():
    pass


@cli.command()
@click.option("--pdf", default=None, help="Path to course PDF")
@click.option("--outline", default=None, help="Path to plain text outline")
@click.option("--course", required=True, help="Course name")
@click.option("--update", is_flag=True, help="Update existing framework")
def fill(pdf, outline, course, update):
    """Fill Mode: generate or update knowledge framework."""
    from fill_mode.parser import extract_text_from_pdf, extract_text_from_outline
    from fill_mode.framework import generate_framework
    from review_mode.rhetoric import extract_rhetoric

    if pdf:
        click.echo(f"Parsing PDF: {pdf}")
        text = extract_text_from_pdf(pdf)
    elif outline:
        text = extract_text_from_outline(outline)
    elif update:
        p = _course_path(course) / "source.txt"
        if not p.exists():
            click.echo("No cached source found. Provide --pdf or --outline.", err=True)
            return
        text = p.read_text(encoding="utf-8")
    else:
        click.echo("Provide --pdf or --outline.", err=True)
        return

    # Cache source text for future updates
    cp = _course_path(course)
    cp.mkdir(parents=True, exist_ok=True)
    (cp / "source.txt").write_text(text, encoding="utf-8")

    click.echo("Generating knowledge framework...")
    nodes = generate_framework(course, text)
    _save_nodes(course, nodes)
    click.echo(f"Framework saved: {len(nodes)} nodes")

    click.echo("Extracting rhetoric...")
    rhetoric_data = extract_rhetoric(course, text)
    import uuid
    from store.schema import RhetoricEntry
    rhetoric = [RhetoricEntry(id=str(uuid.uuid4()), courses=[course], **r) for r in rhetoric_data]
    from dataclasses import asdict
    (cp / "rhetoric.json").write_text(
        json.dumps([asdict(r) for r in rhetoric], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    click.echo(f"Rhetoric saved: {len(rhetoric)} entries")


@cli.command()
@click.option("--course", required=True, help="Course name")
@click.option("--format", "fmt", default="mubu", show_default=True)
def export(course, fmt):
    """Export knowledge framework to Mubu-compatible format."""
    from fill_mode.mubu_export import to_mubu_markdown
    nodes = _load_nodes(course)
    if not nodes:
        click.echo("No framework found. Run 'fill' first.", err=True)
        return
    output = to_mubu_markdown(nodes)
    out_path = _course_path(course) / f"export_{fmt}.md"
    out_path.write_text(output, encoding="utf-8")
    click.echo(f"Exported to {out_path}")
    click.echo("\n" + output)


@cli.command()
@click.option("--question", required=True, help="Essay question")
@click.option("--course", required=True, help="Course name")
def review(question, course):
    """Review Mode: locate relevant nodes and recommend rhetoric."""
    from review_mode.retriever import review_question
    nodes = _load_nodes(course)
    rhetoric = _load_rhetoric(course)
    if not nodes:
        click.echo("No framework found. Run 'fill' first.", err=True)
        return
    click.echo("Analyzing question...")
    result = review_question(question, nodes, rhetoric)
    click.echo("\n=== Relevant Knowledge Nodes ===")
    for n in result.get("relevant_nodes", []):
        click.echo(f"  • {n['title']}")
    click.echo("\n=== Recommended Rhetoric ===")
    for r in result.get("recommended_rhetoric", []):
        click.echo(f"  [{r['context']}]\n  {r['text']}\n")
    click.echo("=== Answer Outline ===")
    for step in result.get("answer_outline", []):
        click.echo(f"  {step}")


if __name__ == "__main__":
    cli()
