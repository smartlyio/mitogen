
#
# Read in series.json describing some pcaps, pull out stats about their TCP
# streams and overlay on a line chart.
#

import csv
import json
import subprocess
import sys

import numpy
import matplotlib.ticker
import matplotlib.pyplot as plt


def parse_capture(path, stream=0):
    fieldnames = [
        'frame.time_epoch',
        #'ip.src',
        'tcp.dstport',
        'tcp.seq',
    ]

    args = [
        'tshark',
        '-r', path,
        '-T', 'fields',
        '-E', 'separator=,',
        '-E', 'occurrence=f',
    ]
    for name in fieldnames:
        args.extend(('-e', name))

    args.append(
        'tcp.stream == %(stream)d &&'
        '(tcp.dstport == 22 || tcp.dstport == 9122)'
        % locals()
    )

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    reader = csv.DictReader(proc.stdout, fieldnames=fieldnames)
    last = None

    ms = []
    sent = []

    for row in reader:
        if last and last['tcp.seq'] == row['tcp.seq']:
            continue  # skip control traffic

        garbage = 1000 * (float(row['frame.time_epoch']))
        ms.append(round(garbage, -2))
        sent.append(int(row['tcp.seq']))
        last = row

    return sent, numpy.asarray(ms)


def cumsum(lst, n):
    if lst:
        lst.append(n + lst[-1])
    else:
        lst.append(n)

import datetime
epoch = datetime.datetime(1970, 1, 1)

def parse_perf(path):
    fp = open(path)
    s = fp.readline()

    dt = datetime.datetime.strptime(
        s.rstrip(),
        '# started on %a %b %d %H:%M:%S %Y',
    )
    start_ts = (dt - epoch).total_seconds()

    fp.readline()
    reader = csv.reader(fp)
    rowi = None
    last = None
    series = {}
    ms = []
    for row in reader:
        if (not last) or row[0] != last[0]:
            last = row
            ms.append(1000 * (start_ts + float(row[0])))
        cumsum(series.setdefault(row[3], []), float(row[1]))

    return series, numpy.asarray(ms)


def format_bytes(n, _=None):
    return '%.02f MiB' % (n / 1048576.0,)


def format_k(n, _=None):
    return '%dk' % (n / 1000.0)


def format_ms(n, _=None):
    return '%.01fs' % (n / 1000.0)


def main():
    figure, (
        timenet,
        task_clock,
        page_faults,
        context_switches,
        migrations,
    ) = plt.subplots(
        5, 1,
        figsize=(10, 7),
        gridspec_kw={
            'height_ratios': [5.5, 2, 2, 2, 2],
        },
        frameon=False,
        sharex=True,
    )
    figure.align_ylabels()
    timenet.set_frame_on(False)
    task_clock.set_frame_on(False)
    page_faults.set_frame_on(False)
    context_switches.set_frame_on(False)
    migrations.set_frame_on(False)

    task_clock.set_ylabel('CPU')
    page_faults.set_ylabel('Faults')
    context_switches.set_ylabel('Switches')
    migrations.set_ylabel('Migrations')
    migrations.set_xlabel('Time')

    timenet.set_ylabel('Bandwidth')
    for ax in (
            timenet, task_clock, page_faults, context_switches, migrations
    ):
        ax.grid(True)
        ax.tick_params(axis='x', color='silver')
        ax.tick_params(axis='y', color='silver')

    timenet.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_bytes)
    )
    timenet.get_xaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_ms)
    )
    page_faults.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_k)
    )
    context_switches.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_k)
    )
    task_clock.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_ms)
    )

    for series in json.loads(open('series.json').read()):
        sent, net_ms = parse_capture(
            path=series['path'],
            stream=series.get('stream', 0),
        )

        pseries, perf_ms = parse_perf(series['path'].split('-')[0] + '-perf.csv')

        label = u'%s \u2013 %s, %s' % (
            series['title'],
            format_bytes(sent[-1]),
            format_ms(max(net_ms) - min(net_ms)),
        )
        timenet.plot(
            net_ms - perf_ms.min(),
            sent,
            label=label,
            linewidth=1,
        )
        task_clock.plot(
            perf_ms - perf_ms.min(),
            pseries['task-clock'],
            linewidth=1,
        )
        page_faults.plot(
            perf_ms - perf_ms.min(),
            pseries['page-faults'],
            linewidth=1,
        )
        context_switches.plot(
            perf_ms - perf_ms.min(),
            pseries['context-switches'],
            linewidth=1,
        )
        migrations.plot(
            perf_ms - perf_ms.min(),
            pseries['cpu-migrations'],
            linewidth=1,
        )

    timenet.legend()
    plt.savefig(
        'output.svg',
        dpi=75,
        bbox_inches='tight',
    )

if __name__ == '__main__':
    main()
