
# watcher_prefix_default = "'migrate' or 'devices'"
# @app.command()  # NoQA
# def start(
#     what: StartArgs = typer.Argument(
#         StartArgs.wh_watcher,
#         help="See documentation or above for info on what each webhook receiver does",
#     ),
#     port: int = typer.Option(config.webhook.port, "-P", "--port", help="Port to listen on (overrides config value if provided)", show_default=True),
#     collect: bool = typer.Option(False, "--collect", "-c", help="Store raw webhooks in local json file", rich_help_panel="Dev Options", hidden=not env.is_dev_user),
#     test_mode: bool = typer.Option(False, "--test-mode", help="Enable test mode [dim italic](Allows hooks with no signature)[/]", rich_help_panel="Dev Options", hidden=not env.is_dev_user),
#     watcher_dir: Path = typer.Option(
#         Path.cwd(),
#         "-D",
#         "--dir",
#         help=f"For [cyan]hook-watcher[/].  Directory to watch for device files defining how to respond to devices going online/offline. {render.help_block(f'current directory ({Path.cwd()})')}",
#         show_default=False,
#         envvar="CENCLI_WATCHER_DIR"
#     ),
#     watcher_prefix: str = typer.Option(None, "--prefix", help=f"filename prefix to watch for.  {render.help_block(watcher_prefix_default)}"),
#     delete_ws: str = typer.Option(
#         None,
#         envvar=env_var.dest_workspace,
#         help=f"The Aruba Central [dim italic]([green]GreenLake[/green])[/] Destination WorkSpace for migration operations.  {emoji.warn} Devices found in watch files will be deleted from this workspace once disconnected.",
#         autocompletion=common.cache.workspace_completion,
#         show_default=False,
#     ),
#     debug: bool = common.options.debug,
#     default: bool = common.options.default,
#     workspace: str = common.options.get("workspace", "--ws", "--workspace", "--move-ws"),
# ) -> None:  # pragma: no cover
#     """Start WebHook Watcher
#         - Watches a directory for import files with specific prefixes.
#         - For new devices.  Automatically performs devices moves (sites/group/label) based on what is defined in the import file.
#         - Also supports ui-only [red]deletes[/] for migration workflow, which will [red]delete[/] the device from the --delete-ws workspace when they go offline.
#         - For migration workflow.  Sites are also deleted, once all devices in that site have been removed.
#         - The Moves/Deletes are performed on intgerval every 10 minutes after the watcher-service is started.
#         - creates the following files:
#         1. watcher-results.csv:  Status of each action attempted (move/delete).  Logs will also have details.
#         2. watcher-staged-move-WORKSPACE_NAME.csv: The staged moves that have yet to be performed (devices have come online).
#         3. watcher-staged-del-WORKSPACE_NAME.csv: The staged deletes if using migrate workflow (devices have gone offline).
#         When moves/deletes are performed the watcher-staged file associated with that action is deleted, and watcher-results.csv is updated with the results.
#         If failures occur, depending on the failure, those devices will remain in the watcher-staged file for retry at the next interval.
#     """
#     if what == StartArgs.wh_watcher:
#         start_webhook_watcher(workspace, watcher_dir=watcher_dir, watcher_prefix=watcher_prefix, port=port, delete_ws=delete_ws, test_mode=test_mode, collect=collect)
#     else:
#         raise NotImplementedError("foreground webhook service start command is only implemented for [cyan]hook-watcher[/].  [cyan]hook-proxy[/] (nms proxy) can be launched in the background using [cyan]cencli start hook-proxy ...[/]")
