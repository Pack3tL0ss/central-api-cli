# completion testing
import typer

if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    from centralcli import cache
    matches = [f"{m[0]}\t{m[1]}" for m in cache.dev_template_completion(sys.argv[-1], sys.argv[1:-1])]
    typer.echo("\n".join(matches))
    ...
