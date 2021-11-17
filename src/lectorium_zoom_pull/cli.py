import logging
import typing as tp

import click

from lectorium_zoom_pull import commands
from lectorium_zoom_pull.config import Config


pass_config = click.make_pass_decorator(Config)


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--download-progress/--no-download-progress', default=True)
@click.option('--secrets-dir', envvar='LZP_SECRETS_DIR')
@click.pass_context
def cli(ctx, debug, download_progress, secrets_dir):
    config = dict()

    if debug is not None:
        config.update(debug=debug)
    if download_progress is not None:
        config.update(download_progress=download_progress)
    if secrets_dir is not None:
        config.update(_secrets_dir=secrets_dir)

    config = Config(**config)

    loglevel = logging.DEBUG if config.debug else logging.INFO
    logging.basicConfig(level=loglevel)

    ctx.obj = config


@cli.command('list')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--topic-contains', multiple=True)
@pass_config
def list_records(
    config: Config,
    from_date,
    to_date,
    topic_contains
):
    topic_contains = list(topic_contains)
    commands.list_records(
        config,
        from_date,
        to_date,
        topic_contains
    )


@cli.command('download')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--meeting-ids')
@click.option('--downloads-dir')
@pass_config
def download_records(
    config: Config,
    from_date,
    to_date,
    meeting_ids,
    downloads_dir
):
    meeting_ids = set(meeting_ids.split(','))
    commands.download_records(
        config,
        from_date,
        to_date,
        meeting_ids,
        downloads_dir
    )
