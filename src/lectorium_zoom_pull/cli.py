import logging
import typing as tp

import click

from lectorium_zoom_pull import commands
from lectorium_zoom_pull.config import Config


pass_config = click.make_pass_decorator(Config)


def make_meeting_filter(
    meeting_ids: str = None,
    topic_contains: tp.Sequence[str] = None,
    topic_regex: str = None,
    host_email_contains: tp.Sequence[str] = None,
    host_email_regex: tp.Sequence[str] = None,
) -> callable:
    filters = [
        meeting_ids,
        topic_contains,
        topic_regex,
        host_email_contains,
        host_email_regex,
    ]
    filters_count = sum(map(lambda arg: 1 if arg else 0, filters))
    if filters_count > 1:
        raise ValueError('Filters are mutually exclusive, specify exactly one')

    if meeting_ids:
        meeting_ids = set(meeting_ids.split(','))
        return commands.Filter.meeting_id_in(meeting_ids)
    elif topic_contains:
        substrings = list(topic_contains)
        return commands.Filter.topic_contains(substrings)
    elif topic_regex:
        expression = topic_regex
        return commands.Filter.topic_regex(expression)
    elif host_email_contains:
        substrings = list(host_email_contains)
        return commands.Filter.host_email_contains(substrings)
    elif host_email_regex:
        expression = host_email_regex
        return commands.Filter.host_email_regex(expression)
    else:
        raise ValueError('Refusing to start without filters, specify exactly one')


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
@click.option('--topic-regex')
@click.option('--host-email-contains', multiple=True)
@click.option('--host-email-regex')
@pass_config
def list_records(
    config: Config,
    from_date,
    to_date,
    topic_contains,
    topic_regex,
    host_email_contains,
    host_email_regex,
):
    meeting_filter = make_meeting_filter(
        topic_contains=topic_contains,
        topic_regex=topic_regex,
        host_email_contains=host_email_contains,
        host_email_regex=host_email_regex,
    )

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
@click.option('--topic-regex')
@click.option('--host-email-contains', multiple=True)
@click.option('--host-email-regex')
@click.option('--downloads-dir', required=True)
@pass_config
def download_records(
    config: Config,
    from_date,
    to_date,
    meeting_ids,
    topic_contains,
    topic_regex,
    host_email_contains,
    host_email_regex,
    downloads_dir
):
    meeting_filter = make_meeting_filter(
        meeting_ids=meeting_ids,
        topic_contains=topic_contains,
        topic_regex=topic_regex,
        host_email_contains=host_email_contains,
        host_email_regex=host_email_regex,
    )

    commands.download_records(
        config,
        from_date,
        to_date,
        meeting_filter,
        downloads_dir
    )
