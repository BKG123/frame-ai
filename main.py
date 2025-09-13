import os
import click
from services.analysis import PhotoAnalyzer


@click.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
@click.option('--output-dir', default='output', help='Directory for edited images')
@click.option('--apply-edits', is_flag=True, help='Generate sample edited versions')
def analyze(image_path, api_key, output_dir, apply_edits):
    """Analyze a photograph and provide professional feedback."""

    click.echo(f"🔍 Analyzing: {image_path}")

    # Initialize analyzer
    analyzer = PhotoAnalyzer(api_key=api_key)

    # Perform analysis
    try:
        analysis = analyzer.analyze_photo(image_path)

        click.echo("\n" + "="*60)
        click.echo("📸 PHOTOGRAPHY ANALYSIS")
        click.echo("="*60)
        click.echo(analysis)

        if apply_edits:
            click.echo("\n" + "="*60)
            click.echo("🎨 APPLYING SAMPLE EDITS")
            click.echo("="*60)

            edit_results = analyzer.suggest_edits(image_path, output_dir)

            for edit_type, result in edit_results.items():
                if 'error' not in edit_type.lower():
                    click.echo(f"✅ {edit_type.title()}: {result}")
                else:
                    click.echo(f"❌ {result}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        if "API key" in str(e):
            click.echo("\n💡 Tip: Set your Anthropic API key with:")
            click.echo("   export ANTHROPIC_API_KEY='your-key-here'")
            click.echo("   or use --api-key flag")


@click.group()
def cli():
    """Frame AI - Your Photography Coach"""
    pass


cli.add_command(analyze)


if __name__ == "__main__":
    cli()
