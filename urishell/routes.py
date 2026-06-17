def register(rt):
    rt.register(
        "shell://{command}",
        "python://urishell.handlers:shell_run",
        kind="command",
        operation="shell.run",
        approval="required",
        side_effects=True,
    )
