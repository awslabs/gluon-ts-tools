import click
import gtstlib


class ArnParamType(click.ParamType):
    name = "arn"

    def convert(self, value, param, ctx):
        try:
            return gtstlib.Arn.parse(value)

        except AssertionError:
            self.fail(f"{value!r} is not a valid arn", param, ctx)


Arn = ArnParamType()


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [
            x for x in self.list_commands(ctx) if x.startswith(cmd_name)
        ]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        ctx.fail(
            f"Too many matches `{cmd_name}` could mean: \n"
            + "\n".join([f"  * {match}" for match in sorted(matches)])
        )


@click.group(cls=AliasedGroup)
def main():
    pass
