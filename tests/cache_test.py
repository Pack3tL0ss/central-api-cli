# completion testing
if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    from centralcli import cache, ic
    "\n".join([ic(f"{c}") for c in cache.dev_template_completion(sys.argv[-1], sys.argv[1:-1])])
