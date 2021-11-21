# lectorium-zoom-pull

Tool to interact with Zoom Cloud Recordings API

# Build and install

```
$ git clone https://github.com/bcskda/lectorium-zoom-pull
$ cd https://github.com/bcskda/lectorium-zoom-pull
$ python3 -m build
$ sudo pip3 install dist/lectorium_zoom_pull-0.0.2-py3-none-any.whl
```

# Quick example

List recent recordings with topics containing "ФПМИ" or "Б05"

```
$ ls secrets
lzp_account_id  lzp_api_key  lzp_api_secret
$ export LZP_SECRETS_DIR=secrets
$ python3 -m lectorium_zoom_pull list \
    --from-date 2021-11-01 \
    --topics-match ФПМИ --topics-match Б05
INFO:root:Total records: 91
1 | MeetingID xxxxxxxxxxxx | 2021-11-01 10:53:01+00:00 | Алгоритмы и структуры данных (YYYY, w семестр), ... (Фамилия И.О.)
```

Download new recordings for specified meeting ids

```
$ ls secrets
lzp_account_id  lzp_api_key  lzp_api_secret
$ export LZP_SECRETS_DIR=secrets
$ python3 -m lectorium_zoom_pull download \
    --downloads-dir ./zoom-recordings
    --from-date 2021-11-01 \
    --meeting-ids xxxxxxxxxxx,zzzzzzzzzzz
INFO:root:Total records: 91                                                                                                                                                                                                           
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording_avo_1280x720.mp4
################################################################################################################################ 100%
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording.m4a
################################################################################################################################ 100%
INFO:root:Downloading xxxxxxxxxxx / GMT20211101-105301_Recording.txt
################################################################################################################################ 100%
1 | MeetingID xxxxxxxxxxx | 2021-11-01 10:53:01+00:00 | Алгоритмы и структуры данных (YYYY, w семестр), ... (Фамилия И.О.) | Fetched 3 files
2 | MeetingID zzzzzzzzzzz  | 2021-11-01 06:57:00+00:00 | Общая физика (YYYY, w семестр), ... (Фамилия И.О.) | Already downloaded
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

Download command can also filter with `--topic-contains`

# Configuration

See [Config class](/src/lectorium_zoom_pull/config.py)

- `account_id` - Zoom account id
- `api_key` - Zoom JWT app Api Key
- `api_secret` - Zoom JWT app Api Secret
- `download_progress` - whether to show curl progressbar (as with `-#`), default on
- `debug` - whether to produce debug logs, default off

Thanks to pydantic, these options can be configured via [secrets files](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support) (also set `RLZ_SECRETS_DIR` or `--secrets-dir`), [environment](https://pydantic-docs.helpmanual.io/usage/settings/#environment-variable-names) (prefixed `LZP_`, case-insensitive) and partially [cli](#global-options)

# CLI

## Global options

- `--help`
- `--(no-)download-progress` - default on
- `--(no-)debug` - default off
- `--secrets-dir` - path to look for configuration, default `/var/run/secrets`

## List options

- `--from-date` - format YYYY-mm-dd, API default is since yesterday
- `--to-date` - format YYYY-mm-dd, API default is up to today
- `--topic-contains` - only show recordings that have certain substring in topic. Can be specified multiple times as "or"

## Donwload options

- `--from-date` - format YYYY-mm-dd, API default is since yesterday
- `--to-date` - format YYYY-mm-dd, API default is up to today
- `--meeting-ids` - comma-separated whitelist of Meeting IDs to download
- `--topic-contains` - same as in `list` command
- `--downloads-dir` - where to save downloads, required

Note that `--meeting-ids` and `--topic-contains` are mutually exclusive
