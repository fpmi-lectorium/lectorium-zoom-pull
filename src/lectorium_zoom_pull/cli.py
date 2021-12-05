import logging
import typing as tp

import click

from lectorium_zoom_pull import commands
from lectorium_zoom_pull.config import Config


pass_config = click.make_pass_decorator(Config)


@click.group()
@click.option('--debug/--no-debug', default=None)
@click.option('--download-progress/--no-download-progress', default=None)
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
@click.option('--host-email-contains', multiple=True)
@pass_config
def list_records(
    config: Config,
    from_date,
    to_date,
    topic_contains,
    host_email_contains,
):
    if topic_contains and host_email_contains:
        logging.error('--topic-contains and --host-email-contains '
                      'are mutually exclusive')

    meeting_filter = None
    if topic_contains:
        substrings = list(topic_contains)
        meeting_filter = commands.filter_topic_contains(substrings)
    elif host_email_contains:
        substrings = list(host_email_contains)
        meeting_filter = commands.filter_host_email_contains(substrings)
    else:
        logging.error('Specify one of: '
                      '--topic-contains, --host-email-contains')

    commands.list_records(
        config,
        from_date,
        to_date,
        meeting_filter
    )


@cli.command('download')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--meeting-ids')
@click.option('--topic-contains', multiple=True)
@click.option('--host-email-contains', multiple=True)
@click.option('--downloads-dir', required=True)
@pass_config
def download_records(
    config: Config,
    from_date,
    to_date,
    meeting_ids,
    topic_contains,
    host_email_contains,
    downloads_dir
):
    if meeting_ids and topic_contains and host_email_contains:
        logging.error('--meeting-ids, --topic-contains and --host-email-contains '
                      'are mutually exclusive')

    meeting_filter = None
    if meeting_ids:
        meeting_ids = set(meeting_ids.split(','))
        meeting_filter = commands.filter_meeting_id_in(meeting_ids)
    elif topic_contains:
        substrings = list(topic_contains)
        meeting_filter = commands.filter_topic_contains(substrings)
    elif host_email_contains:
        substrings = list(host_email_contains)
        meeting_filter = commands.filter_host_email_contains(substrings)
    else:
        logging.error('Specify one of: '
                      '--meeting-ids, --topic-contains, --host-email-contains')

    commands.download_records(
        config,
        from_date,
        to_date,
        meeting_filter,
        downloads_dir
    )
