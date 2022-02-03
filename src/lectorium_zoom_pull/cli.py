import logging
import typing as tp

import click

from lectorium_zoom_pull import commands
from lectorium_zoom_pull.config import Config


pass_config = click.make_pass_decorator(Config)


def make_meeting_filter(
    meeting_ids: str = None,
    topic_contains: tp.Sequence[str] = None,
    not_topic_contains: tp.Sequence[str] = None,
    topic_regex: str = None,
    host_email_contains: tp.Sequence[str] = None,
    host_email_regex: tp.Sequence[str] = None,
) -> callable:
    filters = list()

    if meeting_ids:
        meeting_ids = set(meeting_ids.split(','))
        filters.append(commands.Filter.meeting_id_in(meeting_ids))
    if topic_contains:
        substrings = list(topic_contains)
        filters.append(commands.Filter.topic_contains(substrings))
    if not_topic_contains:
        substrings = list(not_topic_contains)
        positive_filter = commands.Filter.topic_contains(substrings)
        filters.append(lambda meeting: not positive_filter(meeting))
    if topic_regex:
        expression = topic_regex
        filters.append(commands.Filter.topic_regex(expression))
    if host_email_contains:
        substrings = list(host_email_contains)
        filters.append(commands.Filter.host_email_contains(substrings))
    if host_email_regex:
        expression = host_email_regex
        filters.append(commands.Filter.host_email_regex(expression))

    if filters:
        return commands.Filter.conjunction(filters)
    else:
        raise ValueError('Refusing to start without filters, specify at least one')


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
@click.option('--not-topic-contains', multiple=True)
@click.option('--topic-regex')
@click.option('--host-email-contains', multiple=True)
@click.option('--host-email-regex')
@pass_config
def list_records(
    config: Config,
    from_date,
    to_date,
    topic_contains,
    not_topic_contains,
    topic_regex,
    host_email_contains,
    host_email_regex,
):
    meeting_filter = make_meeting_filter(
        topic_contains=topic_contains,
        not_topic_contains=not_topic_contains,
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
@click.option('--not-topic-contains', multiple=True)
@click.option('--topic-regex')
@click.option('--host-email-contains', multiple=True)
@click.option('--host-email-regex')
@click.option('--downloads-dir', required=True)
@click.option('--trash-after-download/--no-trash-after-download', default=False)
@click.option('--csv-log', required=True)
@click.option('--csv-paths-relative-to', required=True)
@pass_config
def download_records(
    config: Config,
    from_date,
    to_date,
    meeting_ids,
    topic_contains,
    not_topic_contains,
    topic_regex,
    host_email_contains,
    host_email_regex,
    downloads_dir,
    trash_after_download,
    csv_log,
    csv_paths_relative_to,
):
    meeting_filter = make_meeting_filter(
        meeting_ids=meeting_ids,
        topic_contains=topic_contains,
        not_topic_contains=not_topic_contains,
        topic_regex=topic_regex,
        host_email_contains=host_email_contains,
        host_email_regex=host_email_regex,
    )

    commands.download_records(
        config,
        from_date,
        to_date,
        meeting_filter,
        downloads_dir,
        trash_after_download,
        csv_log,
        csv_paths_relative_to,
    )


@cli.command('restore-trashed')
@click.option('--meeting-ids')
@click.option('--topic-contains', multiple=True)
@click.option('--not-topic-contains', multiple=True)
@click.option('--topic-regex')
@click.option('--host-email-contains', multiple=True)
@click.option('--host-email-regex')
@pass_config
def restore_trashed(
    config: Config,
    meeting_ids,
    topic_contains,
    not_topic_contains,
    topic_regex,
    host_email_contains,
    host_email_regex,
):
    meeting_filter = make_meeting_filter(
        meeting_ids=meeting_ids,
        topic_contains=topic_contains,
        not_topic_contains=not_topic_contains,
        topic_regex=topic_regex,
        host_email_contains=host_email_contains,
        host_email_regex=host_email_regex,
    )

    commands.restore_trashed_records(
        config,
        meeting_filter,
    )
