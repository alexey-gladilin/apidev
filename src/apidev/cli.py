import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apidev",
        description="apidev contract-driven API generator",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize apidev project directory")
    init_parser.add_argument("--project-dir", default=".")
    init_parser.add_argument(
        "--repair",
        action="store_true",
        help="Repair missing/invalid init-managed files (does not overwrite valid ones).",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite all init-managed files with defaults.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate contracts and rules")
    validate_parser.add_argument("--project-dir", default=".")
    validate_parser.add_argument("--json", dest="json_output", action="store_true")

    diff_parser = subparsers.add_parser("diff", help="Preview generated file changes")
    diff_parser.add_argument("--project-dir", default=".")
    diff_parser.add_argument("--json", dest="json_output", action="store_true")
    diff_parser.add_argument("--scaffold", action="store_true")
    diff_parser.add_argument("--no-scaffold", action="store_true")
    diff_parser.add_argument("--compatibility-policy", default=None)
    diff_parser.add_argument("--baseline-ref", default=None)

    gen_parser = subparsers.add_parser("gen", help="Generate code from contracts")
    gen_parser.add_argument("--project-dir", default=".")
    gen_parser.add_argument("--check", action="store_true")
    gen_parser.add_argument("--json", dest="json_output", action="store_true")
    gen_parser.add_argument("--scaffold", action="store_true")
    gen_parser.add_argument("--no-scaffold", action="store_true")
    gen_parser.add_argument("--compatibility-policy", default=None)
    gen_parser.add_argument("--baseline-ref", default=None)
    gen_parser.add_argument("--include-endpoint", action="append", default=[])
    gen_parser.add_argument("--exclude-endpoint", action="append", default=[])

    generate_parser = subparsers.add_parser("generate", help=argparse.SUPPRESS)
    generate_parser.add_argument("--project-dir", default=".")
    generate_parser.add_argument("--check", action="store_true")
    generate_parser.add_argument("--json", dest="json_output", action="store_true")
    generate_parser.add_argument("--scaffold", action="store_true")
    generate_parser.add_argument("--no-scaffold", action="store_true")
    generate_parser.add_argument("--compatibility-policy", default=None)
    generate_parser.add_argument("--baseline-ref", default=None)
    generate_parser.add_argument("--include-endpoint", action="append", default=[])
    generate_parser.add_argument("--exclude-endpoint", action="append", default=[])

    return parser


def _dispatch_fast(argv: list[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        from apidev.commands.init_cmd import init_command

        init_command(
            project_dir=Path(args.project_dir),
            repair=args.repair,
            force=args.force,
        )
        return 0

    if args.command == "validate":
        from apidev.commands.validate_cmd import validate_command

        validate_command(
            project_dir=Path(args.project_dir),
            json_output=args.json_output,
        )
        return 0

    if args.command == "diff":
        from apidev.commands.diff_cmd import diff_command

        diff_command(
            project_dir=Path(args.project_dir),
            json_output=args.json_output,
            scaffold=args.scaffold,
            no_scaffold=args.no_scaffold,
            compatibility_policy=args.compatibility_policy,
            baseline_ref=args.baseline_ref,
        )
        return 0

    if args.command in {"gen", "generate"}:
        from apidev.commands.generate_cmd import generate_command

        generate_command(
            project_dir=Path(args.project_dir),
            check=args.check,
            json_output=args.json_output,
            scaffold=args.scaffold,
            no_scaffold=args.no_scaffold,
            compatibility_policy=args.compatibility_policy,
            baseline_ref=args.baseline_ref,
            include_endpoint=args.include_endpoint,
            exclude_endpoint=args.exclude_endpoint,
        )
        return 0

    parser.print_help()
    return 0


def _build_typer_app():
    from typer import Context, Exit, Typer, echo

    from apidev.commands.diff_cmd import diff_command
    from apidev.commands.generate_cmd import generate_command
    from apidev.commands.init_cmd import init_command
    from apidev.commands.validate_cmd import validate_command

    app = Typer(
        help="apidev contract-driven API generator",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.callback(invoke_without_command=True)
    def _default_help(ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            echo(ctx.get_help())
            raise Exit(0)

    app.command("init", help="Initialize apidev project directory")(init_command)
    app.command("validate", help="Validate contracts and rules")(validate_command)
    app.command("diff", help="Preview generated file changes")(diff_command)
    app.command("gen", help="Generate code from contracts")(generate_command)
    app.command("generate", hidden=True)(generate_command)
    return app


def main() -> None:
    try:
        raise SystemExit(_dispatch_fast(sys.argv[1:]))
    except SystemExit as exc:
        raise SystemExit(exc.code)


# Keep Typer app available for test harnesses and compatibility with CliRunner imports.
if __name__ != "__main__":
    app = _build_typer_app()


if __name__ == "__main__":
    main()
