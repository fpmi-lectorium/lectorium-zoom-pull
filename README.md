# lectorium-zoom-pull

Tool to interact with Zoom Cloud Recordings API

# Build and install

```
$ git clone https://github.com/bcskda/lectorium-zoom-pull
$ cd https://github.com/bcskda/lectorium-zoom-pull
$ python3 -m build
$ sudo pip3 install dist/lectorium_zoom_pull-$VERSION-py3-none-any.whl
```

# Configuration

Zoom-related parameters are better read from files:

1. Fill `secrets/lzp_{account_id,api_key,api_secret}`
2. Specify `--secrets-dir` before command, e.g. `python -m lectorium_zoom_pull --secrets-dir /etc/lectorium list`

All global parameters:

- `account_id` - Zoom account id
- `api_key` - Zoom JWT app Api Key
- `api_secret` - Zoom JWT app Api Secret
- `download_progress` - whether to show curl progressbar (as with `curl -#`), default off
- `debug` - whether to produce debug logs, default off

Thanks to pydantic, these options can be configured via

- [secret files](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support) (remember to set `LZP_SECRETS_DIR` or `--secrets-dir`)
- [environment](https://pydantic-docs.helpmanual.io/usage/settings/#environment-variable-names) (prefixed `LZP_`, case-insensitive)
- and partially [cli](#global-options)

# CLI

## Global options

- `--help` - list commands
- `--(no-)download-progress` - per-file download progress bar, default off
- `--(no-)debug` - set loglevel to DEBUG, default off
- `--secrets-dir` - path to look for [configuration](#configuration), default `/var/run/secrets`

## Specifying time ranges

- `--from-date` - format YYYY-mm-dd, API default is since yesterday
- `--to-date` - format YYYY-mm-dd, API default is up to today

__Important note: maximum allowed range is one month__.
Longer range will be shrinked silently by API.

## Filtering meetings

Some filters cannot be applied to some commands, see `... COMMAND --help` for details

Specifying a filter several times collects its arguments, e.g. `--topic-contains pea --topic-contains tree`

Specifying multiple different filters results in conjunction

Manpage-like list of all filters:

- `[--meeting-ids YYY,ZZZ,...]` - comma-separated whitelist of Meeting IDs to download
- `[--topic-contains SUBSTRING] ...` - an allowlist of topic substrings
- `[--not-topic-contains SUBSTRING] ...` - a separate blocklist of topic substrings
- `[--topic-regex REGEX]` - partial match of regular expression in topic
- `[--host-email-contains SUBSTRING] ...` - certain substring in host email
- `[--host-email-regex REGEX]` - partial match of regular expression in host email

## `list` command arguments

- [time range](#specifying-time-ranges), default is yesterday and today
- any non-empty combination of [meeting filters](#filtering-meetings), required

## `download` command arguments

- [time range](#specifying-time-ranges), default is yesterday and today
- any non-empty combination of [meeting filters](#filtering-meetings), required
- `--downloads-dir` - where to save downloads, required
- `--(no-)trash-after-download` - whether to trash recordings after downloading, default is off

## `restore-trashed` command arguments
- any non-empty combination of [meeting filters](#filtering-meetings), required
- _CURRENTLY UNSUPPORTED_: [time range](#specifying-time-ranges)

# Examples

List recent recordings with topics containing "ФПМИ" or "Б05"

```
$ ls secrets
lzp_account_id  lzp_api_key  lzp_api_secret
$ export LZP_SECRETS_DIR=secrets
$ python3 -m lectorium_zoom_pull list \
    --from-date 2021-11-01 --to-date 2021-12-01 \
    --topic-regex 'ФПМИ|Б05'
INFO:root:Total records: 91
1 | MeetingID xxxxxxxxxxxx | 2021-11-01 10:53:01+00:00 | Алгоритмы и структуры данных (YYYY, w семестр), ... (Фамилия И.О.)
```

Download and move to trash new recordings for specified meeting ids

```
$ ls secrets
lzp_account_id  lzp_api_key  lzp_api_secret
$ export LZP_SECRETS_DIR=secrets
$ python3 -m lectorium_zoom_pull download \
    --downloads-dir ./zoom-recordings
    --from-date 2021-11-01 --to-date 2021-12-01 \
    --meeting-ids xxxxxxxxxxx,zzzzzzzzzzz \
    --trash-after-download
INFO:root:Total records: 91                                                                                                                                                                                                           
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording_avo_1280x720.mp4
################################################################################################################################ 100%
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording.m4a
################################################################################################################################ 100%
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording.txt
################################################################################################################################ 100%
1 | MeetingID xxxxxxxxxxx | 2021-11-01 10:53:01+00:00 | Алгоритмы и структуры данных (YYYY, w семестр), ... (Фамилия И.О.) | Fetched 3 files / Trashed
2 | MeetingID zzzzzzzzzzz  | 2021-11-01 06:57:00+00:00 | Общая физика (YYYY, w семестр), ... (Фамилия И.О.) | Already downloaded / Trashed
$ tree ./zoom-recordings
./zoom-recorings
└── 2021.11 - ноябрь
    └── 2021.11.01
        └── Алгоритмы и структуры данных (YYYY, w семестр), ... (Фамилия И.О.) xxxxxxxxxxx
            ├── GMT20211101-105301_Recording_avo_1280x720.mp4
            └── GMT20211101-105301_Recording.m4a
            └── GMT20211101-105301_Recording.txt
        └── Общая физика (YYYY, w семестр), ... (Фамилия И.О.) zzzzzzzzzzz
            ├── GMT20211101-065700_Recording_avo_1280x720.mp4
            └── GMT20211101-065700_Recording.m4a
            └── GMT20211101-065700_Recording.txt

4 directories, 6 files
```
