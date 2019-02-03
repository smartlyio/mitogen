
#
# Read in series.json describing some pcaps, pull out stats about their TCP
# streams and overlay on a line chart.
#

import csv
import json
import subprocess
import sys

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

    start_ts = None
    ms = []
    sent = []

    for row in reader:
        if last is None:
            start_ts = float(row['frame.time_epoch'])
        elif last['tcp.seq'] == row['tcp.seq']:
            continue  # skip control traffic

        garbage = 1000 * (float(row['frame.time_epoch']) - start_ts)
        ms.append(round(garbage, -2))
        sent.append(int(row['tcp.seq']))
        last = row

    return sent, ms


def format_bytes(n, _=None):
    return '%.02f MiB' % (n / 1048576.0,)


def format_ms(n, _=None):
    return '%.01fs' % (n / 1000.0)


def main():
    figure = plt.figure(figsize=(11, 4), frameon=False)
    subplot = figure.add_subplot(1, 1, 1, frameon=False)
    subplot.set_ylabel('Bandwidth')
    subplot.set_xlabel('Time')
    subplot.tick_params(axis='x', color='silver')
    subplot.tick_params(axis='y', color='silver')
    subplot.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_bytes)
    )
    subplot.get_xaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(format_ms)
    )
    plt.grid()

    for series in json.loads(open('series.json').read()):
        sent, ms = parse_capture(
            path=series['path'],
            stream=series.get('stream', 0),
        )
        label = u'%s \u2013 %s, %s' % (
            series['title'],
            format_bytes(sent[-1]),
            format_ms(ms[-1]),
        )
        subplot.plot(ms, sent,
            label=label,
            linewidth=1.5,
        )

    plt.legend()
    plt.savefig('output.svg', dpi=275, bbox_inches='tight')

if __name__ == '__main__':
    main()
